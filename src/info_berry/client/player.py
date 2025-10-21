from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from info_berry.client.config import AppConfig, load_config
from info_berry.client.content import ContentBank
from info_berry.client.display import Display

logger = logging.getLogger(__name__)


class Player:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self._cfg: AppConfig = load_config(config_file)
        self._bank = ContentBank(self._cfg.contents)
        self._display = Display(
            screen=self._cfg.display.screen,
            width=self._cfg.display.width,
            height=self._cfg.display.height,
            rotation=self._cfg.display.rotation,
        )
        self._tasks: dict[str, asyncio.Task] = {}
        self._shutdown = asyncio.Event()
        self._lock = asyncio.Lock()
        path = Path(config_file)
        self._last_mtime = path.stat().st_mtime if path.exists() else None

    async def run(self):
        await self._display.launch()
        await self._display.ensure_pages([c.to_url() for c in self._bank.items()])
        self._tasks["rotate"] = asyncio.create_task(self._rotate_loop(), name="rotate")
        self._tasks["cfgwatch"] = asyncio.create_task(
            self._config_watch_loop(), name="cfgwatch"
        )
        if self._cfg.behavior.refresh_interval:
            self._tasks["refresh"] = asyncio.create_task(
                self._refresh_loop(), name="refresh"
            )
        await self._shutdown.wait()
        await self.cleanup()

    async def stop(self):
        self._shutdown.set()

    async def cleanup(self):
        for t in list(self._tasks.values()):
            t.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        await self._display.close()

    async def _rotate_loop(self):
        while not self._shutdown.is_set():
            try:
                idx, cur = self._bank.current()
                await self._display.show(idx)
                dur = max(
                    1,
                    int(
                        self._bank.duration_for(
                            cur, self._cfg.behavior.rotation_interval
                        )
                    ),
                )
                logger.debug(
                    "rotate index=%s type=%s src=%s duration=%ss",
                    idx,
                    getattr(cur, "kind", "url"),
                    cur.source,
                    dur,
                )
                try:
                    await asyncio.wait_for(self._shutdown.wait(), timeout=dur)
                except asyncio.TimeoutError:
                    pass
                self._bank.next_index()
            except Exception as e:
                # Never let the task die silently; log and continue
                logger.exception("rotation tick failed: %s", e)
                await asyncio.sleep(1)

    async def _refresh_loop(self):
        interval = int(self._cfg.behavior.refresh_interval)
        while not self._shutdown.is_set():
            try:
                await asyncio.wait_for(self._shutdown.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
            idx, _ = self._bank.current()
            await self._display.reload(idx)

    async def _config_watch_loop(self):
        path = Path(self.config_file)
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(1)
                if not path.exists():
                    continue
                mtime = path.stat().st_mtime
                if self._last_mtime is None or mtime <= self._last_mtime:
                    continue
                self._last_mtime = mtime
                await self._reload_config()
            except Exception as e:
                logger.exception("config watch error: %s", e)

    async def _reload_config(self):
        async with self._lock:
            new_cfg = load_config(self.config_file)
            disp_changed = new_cfg.display != self._cfg.display
            self._cfg = new_cfg
            diff = self._bank.diff(new_cfg.contents)
            self._bank.set_items(new_cfg.contents)
            urls = [c.to_url() for c in self._bank.items()]
            if disp_changed:
                await self._display.close()
                await self._display.launch()
            await self._display.ensure_pages(urls)
            logger.info(
                "config reloaded added=%s removed=%s modified=%s",
                diff["added"],
                diff["removed"],
                diff["modified"],
            )
