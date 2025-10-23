from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess
from typing import List, Optional

from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)


class Display:
    """Playwright-backed view: manages browser lifecycle and pages."""

    def __init__(
        self, screen=":0", width=1920, height=1080, rotation: Optional[str] = None
    ):
        self.screen = screen
        self.width = width
        self.height = height
        self.rotation = rotation
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context = None
        self._pages = []
        self._urls: List[str] = []
        self._lock = asyncio.Lock()

    async def launch(self):
        is_linux = platform.system() == "Linux"
        is_macos = platform.system() == "Darwin"

        if is_linux:
            os.environ["DISPLAY"] = self.screen
            subprocess.run(["xset", "-dpms"], check=False)
            subprocess.run(["xset", "s", "off"], check=False)
            subprocess.run(["xset", "s", "noblank"], check=False)
            if self.rotation:
                subprocess.run(
                    ["xrandr", "--output", "HDMI-1", "--rotate", self.rotation],
                    check=False,
                )

        self._playwright = await async_playwright().start()

        launch_args = []
        if is_linux:
            launch_args += ["--kiosk"]
        elif is_macos:
            launch_args += [
                "--start-maximized",
                "--disable-session-crashed-bubble",
                "--disable-features=TranslateUI",
            ]

        self._browser = await self._playwright.chromium.launch(
            headless=False,
            args=launch_args
            + [
                "--disable-infobars",
                "--noerrdialogs",
                "--autoplay-policy=no-user-gesture-required",
            ],
        )
        self._context = await self._browser.new_context(
            viewport=None,
            no_viewport=True,
        )

    async def ensure_pages(self, urls: List[str]):
        async with self._lock:
            if self._context is None:
                raise RuntimeError("Display not launched")
            while len(self._pages) < len(urls):
                p = await self._context.new_page()
                await p.goto("about:blank")
                self._pages.append(p)
            while len(self._pages) > len(urls):
                p = self._pages.pop()
                try:
                    await p.close()
                except Exception:
                    logger.exception("closing extra page failed")
            for i, url in enumerate(urls):
                if i >= len(self._urls) or self._urls[i] != url:
                    await self._pages[i].goto(
                        url, wait_until="domcontentloaded", timeout=30000
                    )
            self._urls = urls[:]

    async def show(self, index: int):
        async with self._lock:
            if not self._pages:
                return
            index = max(0, min(index, len(self._pages) - 1))
            await self._pages[index].bring_to_front()

    async def reload(self, index: int):
        async with self._lock:
            if 0 <= index < len(self._pages):
                await self._pages[index].reload(
                    wait_until="domcontentloaded", timeout=30000
                )

    async def close(self):
        async with self._lock:
            try:
                if self._context is not None:
                    await self._context.close()
            except Exception:
                logger.debug("context already closed", exc_info=True)
            finally:
                self._context = None

            self._pages.clear()
            self._urls.clear()

            try:
                if self._browser is not None:
                    await self._browser.close()
            except Exception:
                logger.debug("browser already closed", exc_info=True)
            finally:
                self._browser = None

            try:
                if self._playwright is not None:
                    await self._playwright.stop()
            except Exception:
                logger.debug("playwright already stopped", exc_info=True)
            finally:
                self._playwright = None
