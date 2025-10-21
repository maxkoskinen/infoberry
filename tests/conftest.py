"""Shared fixtures for all tests."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml


@pytest.fixture
def sample_config_dict() -> dict:
    """Sample configuration dictionary."""
    return {
        "display": {
            "screen": ":0",
            "width": 1920,
            "height": 1080,
            "rotation": None,
        },
        "behavior": {
            "rotation_interval": 30,
            "refresh_interval": 300,
        },
        "content": [
            {"type": "url", "source": "https://example.com", "duration": 10},
            {"type": "html", "source": "/path/to/file.html", "duration": 20},
            {"type": "image", "source": "/path/to/image.png", "duration": 15},
        ],
    }


@pytest.fixture
def temp_config_file(
    sample_config_dict: dict, tmp_path: Path
) -> Generator[Path, None, None]:
    """Create a temporary config file."""
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text(yaml.dump(sample_config_dict))
    yield config_file


@pytest.fixture
def mock_playwright():
    """Mock playwright context."""
    mock = MagicMock()
    mock.chromium.launch = AsyncMock()
    mock.stop = AsyncMock()
    return mock


@pytest.fixture
def mock_browser():
    """Mock browser instance."""
    browser = MagicMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_context():
    """Mock browser context."""
    context = MagicMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_page():
    """Mock page instance."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.bring_to_front = AsyncMock()
    page.reload = AsyncMock()
    page.close = AsyncMock()
    return page
