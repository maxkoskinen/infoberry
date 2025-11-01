from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from info_berry.client.player import Player


def parse_args():
    p = argparse.ArgumentParser(description="infoberry client")
    _ = p.add_argument(
        "-c",
        "--config",
        default=str(Path.cwd() / "client-config.yaml"),
        help="Path to YAML config file",
        required=True,
    )
    _ = p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    return p.parse_args()


async def _amain(config_path: str):
    player = Player(config_file=config_path)
    loop = asyncio.get_running_loop()

    def _stop():
        _ = asyncio.create_task(player.stop())

    try:
        loop.add_signal_handler(signal.SIGINT, _stop)
        loop.add_signal_handler(signal.SIGTERM, _stop)
    except NotImplementedError:
        # Windows fallback
        pass
    await player.run()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),  # pyright: ignore[reportAny]
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )
    try:
        asyncio.run(_amain(args.config))  # pyright: ignore[reportAny]
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
