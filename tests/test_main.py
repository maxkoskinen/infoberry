"""Tests for main module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from info_berry.client.main import _amain, main, parse_args


class TestParseArgs:
    """Tests for argument parsing."""

    def test_parse_args_with_config(self):
        """Test parsing with config argument."""
        test_args = ["-c", "/path/to/config.yaml"]
        with patch.object(sys, "argv", ["main.py"] + test_args):
            args = parse_args()
            assert args.config == "/path/to/config.yaml"
            assert args.log_level == "INFO"

    def test_parse_args_with_log_level(self):
        """Test parsing with log level."""
        test_args = ["-c", "/path/to/config.yaml", "--log-level", "DEBUG"]
        with patch.object(sys, "argv", ["main.py"] + test_args):
            args = parse_args()
            assert args.log_level == "DEBUG"

    def test_parse_args_requires_config(self):
        """Test that config is required."""
        with patch.object(sys, "argv", ["main.py"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestAmain:
    """Tests for _amain function."""

    @pytest.mark.asyncio
    async def test_amain_creates_player(self, temp_config_file: Path):
        """Test _amain creates and runs player."""
        with patch("info_berry.client.main.Player") as MockPlayer:
            mock_player = MagicMock()
            mock_player.run = AsyncMock()
            mock_player.stop = AsyncMock()
            MockPlayer.return_value = mock_player

            # Immediately stop to prevent hanging
            async def stop_immediately():
                await mock_player.stop()

            mock_player.run.side_effect = stop_immediately

            try:
                await _amain(str(temp_config_file))
            except Exception:
                pass

            MockPlayer.assert_called_once_with(config_file=str(temp_config_file))

    @pytest.mark.asyncio
    async def test_amain_handles_signal(self, temp_config_file: Path):
        """Test _amain sets up signal handlers."""
        with patch("info_berry.client.main.Player") as MockPlayer:
            mock_player = MagicMock()
            mock_player.run = AsyncMock()
            mock_player.stop = AsyncMock()
            MockPlayer.return_value = mock_player

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_event_loop = MagicMock()
                mock_loop.return_value = mock_event_loop

                async def stop_immediately():
                    pass

                mock_player.run.side_effect = stop_immediately

                try:
                    await _amain(str(temp_config_file))
                except Exception:
                    pass

                # Should attempt to add signal handlers
                assert mock_event_loop.add_signal_handler.called


class TestMain:
    """Tests for main function."""

    def test_main_parses_args(self, temp_config_file: Path):
        """Test main parses arguments."""
        test_args = ["-c", str(temp_config_file)]
        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("asyncio.run") as mock_run:
                main()
                mock_run.assert_called_once()

    def test_main_handles_keyboard_interrupt(self, temp_config_file: Path):
        """Test main handles KeyboardInterrupt gracefully."""
        test_args = ["-c", str(temp_config_file)]
        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("asyncio.run", side_effect=KeyboardInterrupt):
                # Should not raise exception
                main()

    def test_main_configures_logging(self, temp_config_file: Path):
        """Test main configures logging."""
        test_args = ["-c", str(temp_config_file), "--log-level", "DEBUG"]
        with patch.object(sys, "argv", ["main.py"] + test_args):
            with patch("logging.basicConfig") as mock_logging:
                with patch("asyncio.run"):
                    main()
                    mock_logging.assert_called_once()
