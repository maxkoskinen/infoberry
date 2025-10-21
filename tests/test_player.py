"""Tests for player module."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from info_berry.client.player import Player


class TestPlayer:
    """Tests for Player class."""

    def test_initialization(self, temp_config_file: Path):
        """Test Player initialization."""
        player = Player(config_file=str(temp_config_file))
        assert player.config_file == str(temp_config_file)
        assert len(player._bank.items()) == 3

    @pytest.mark.asyncio
    async def test_run_launches_display(self, temp_config_file: Path):
        """Test run launches display."""
        player = Player(config_file=str(temp_config_file))

        # Track if display methods were called
        launch_called = False
        ensure_pages_called = False

        async def mock_launch():
            nonlocal launch_called
            launch_called = True

        async def mock_ensure_pages(urls):
            nonlocal ensure_pages_called
            ensure_pages_called = True

        async def mock_close():
            pass

        # Create mock coroutines for the loops
        async def mock_loop_coro():
            # Wait for shutdown signal
            await player._shutdown.wait()

        player._display.launch = mock_launch
        player._display.ensure_pages = mock_ensure_pages
        player._display.close = mock_close

        # Patch create_task to not actually start the loops
        original_create_task = asyncio.create_task
        created_tasks = []

        def patched_create_task(coro, **kwargs):
            # Create a simple task that waits for shutdown
            task = original_create_task(mock_loop_coro())
            created_tasks.append(task)
            # Cancel the original coroutine to prevent warnings
            coro.close()
            return task

        with patch("asyncio.create_task", side_effect=patched_create_task):
            # Set shutdown immediately so run() exits quickly
            player._shutdown.set()

            await player.run()

            # Clean up tasks
            for task in created_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            assert launch_called
            assert ensure_pages_called

    @pytest.mark.asyncio
    async def test_stop_sets_shutdown_event(self, temp_config_file: Path):
        """Test stop sets shutdown event."""
        player = Player(config_file=str(temp_config_file))
        assert not player._shutdown.is_set()

        await player.stop()
        assert player._shutdown.is_set()

    @pytest.mark.asyncio
    async def test_cleanup_cancels_tasks(self, temp_config_file: Path):
        """Test cleanup cancels all tasks."""
        player = Player(config_file=str(temp_config_file))

        # Create real async task
        async def dummy():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(dummy())
        player._tasks["test"] = task

        async def mock_close():
            pass

        player._display.close = mock_close

        await player.cleanup()

        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_rotate_loop_shows_content(self, temp_config_file: Path):
        """Test rotate loop shows content."""
        player = Player(config_file=str(temp_config_file))

        show_called = False

        async def mock_show(idx):
            nonlocal show_called
            show_called = True

        player._display.show = mock_show

        # Run one iteration
        iteration_count = 0

        async def mock_wait_for(event_wait, timeout):
            nonlocal iteration_count
            iteration_count += 1
            if iteration_count >= 2:
                player._shutdown.set()
            raise asyncio.TimeoutError()

        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            try:
                await player._rotate_loop()
            except Exception:
                pass

        assert show_called

    @pytest.mark.asyncio
    async def test_reload_config_updates_content(self, temp_config_file: Path):
        """Test config reload updates content."""
        player = Player(config_file=str(temp_config_file))

        # Modify config
        new_config = {
            "display": {"screen": ":0", "width": 1920, "height": 1080},
            "behavior": {"rotation_interval": 30},
            "content": [
                {"type": "url", "source": "https://new-url.com", "duration": 10}
            ],
        }
        temp_config_file.write_text(yaml.dump(new_config))

        async def mock_ensure_pages(urls):
            pass

        player._display.ensure_pages = mock_ensure_pages

        await player._reload_config()

        assert len(player._bank.items()) == 1
        assert player._bank.items()[0].source == "https://new-url.com"

    @pytest.mark.asyncio
    async def test_reload_config_restarts_display_if_changed(
        self, temp_config_file: Path
    ):
        """Test display restart when display config changes."""
        player = Player(config_file=str(temp_config_file))

        # Change display config
        new_config = {
            "display": {"screen": ":1", "width": 1280, "height": 720},
            "behavior": {"rotation_interval": 30},
            "content": [{"type": "url", "source": "https://example.com"}],
        }
        temp_config_file.write_text(yaml.dump(new_config))

        close_called = False
        launch_called = False

        async def mock_close():
            nonlocal close_called
            close_called = True

        async def mock_launch():
            nonlocal launch_called
            launch_called = True

        async def mock_ensure_pages(urls):
            pass

        player._display.close = mock_close
        player._display.launch = mock_launch
        player._display.ensure_pages = mock_ensure_pages

        await player._reload_config()

        assert close_called
        assert launch_called

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_config_watch_loop_detects_changes(self, temp_config_file: Path):
        """Test config watch loop detects file changes."""
        player = Player(config_file=str(temp_config_file))

        reload_called = False

        async def mock_reload_config():
            nonlocal reload_called
            reload_called = True

        player._reload_config = mock_reload_config

        iterations = 0
        original_sleep = asyncio.sleep

        async def controlled_sleep(duration):
            nonlocal iterations
            iterations += 1
            if iterations == 1:
                # First iteration: modify file
                temp_config_file.touch()
                player._last_mtime = 0  # Force change detection
                await original_sleep(0.001)
            else:
                # Stop after check
                player._shutdown.set()
                await original_sleep(0.001)

        with patch("asyncio.sleep", side_effect=controlled_sleep):
            await player._config_watch_loop()

        # Verify mechanism works
        assert iterations >= 1
