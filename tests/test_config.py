"""Tests for config module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from info_berry.client.config import (
    AppConfig,
    BehaviorConfig,
    DisplayConfig,
    _to_content,
    load_config,
)
from info_berry.client.content import (
    HtmlFileContent,
    ImageContent,
    UrlContent,
    VideoContent,
)


class TestDisplayConfig:
    """Tests for DisplayConfig dataclass."""

    def test_default_values(self):
        """Test DisplayConfig with default values."""
        config = DisplayConfig()
        assert config.screen == ":0"
        assert config.width == 1920
        assert config.height == 1080
        assert config.rotation is None

    def test_custom_values(self):
        """Test DisplayConfig with custom values."""
        config = DisplayConfig(screen=":1", width=1280, height=720, rotation="left")
        assert config.screen == ":1"
        assert config.width == 1280
        assert config.height == 720
        assert config.rotation == "left"


class TestBehaviorConfig:
    """Tests for BehaviorConfig dataclass."""

    def test_default_values(self):
        """Test BehaviorConfig with default values."""
        config = BehaviorConfig()
        assert config.rotation_interval == 30
        assert config.refresh_interval is None

    def test_custom_values(self):
        """Test BehaviorConfig with custom values."""
        config = BehaviorConfig(rotation_interval=60, refresh_interval=300)
        assert config.rotation_interval == 60
        assert config.refresh_interval == 300


class TestToContent:
    """Tests for _to_content function."""

    def test_url_content_creation(self):
        """Test creating UrlContent."""
        obj = {"type": "url", "source": "https://example.com", "duration": 10}
        content = _to_content(obj)
        assert isinstance(content, UrlContent)
        assert content.source == "https://example.com"
        assert content.duration == 10

    def test_html_content_creation(self):
        """Test creating HtmlFileContent."""
        obj = {"type": "html", "source": "/path/to/file.html", "duration": 20}
        content = _to_content(obj)
        assert isinstance(content, HtmlFileContent)
        assert content.source == "/path/to/file.html"
        assert content.duration == 20

    def test_image_content_creation(self):
        """Test creating ImageContent."""
        obj = {"type": "image", "source": "/path/to/image.png", "duration": 15}
        content = _to_content(obj)
        assert isinstance(content, ImageContent)
        assert content.source == "/path/to/image.png"
        assert content.duration == 15

    def test_video_content_creation(self):
        """Test creating VideoContent."""
        obj = {"type": "video", "source": "/path/to/video.mp4", "duration": 30}
        content = _to_content(obj)
        assert isinstance(content, VideoContent)
        assert content.source == "/path/to/video.mp4"
        assert content.duration == 30

    def test_default_to_url_content(self):
        """Test unknown type defaults to UrlContent."""
        obj = {"type": "unknown", "source": "https://example.com", "duration": 10}
        content = _to_content(obj)
        assert isinstance(content, UrlContent)

    def test_missing_type_defaults_to_url(self):
        """Test missing type defaults to UrlContent."""
        obj = {"source": "https://example.com", "duration": 10}
        content = _to_content(obj)
        assert isinstance(content, UrlContent)

    def test_without_duration(self):
        """Test content creation without duration."""
        obj = {"type": "url", "source": "https://example.com"}
        content = _to_content(obj)
        assert content.duration is None


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, temp_config_file: Path):
        """Test loading valid configuration file."""
        config = load_config(str(temp_config_file))
        assert isinstance(config, AppConfig)
        assert config.display.width == 1920
        assert config.display.height == 1080
        assert config.behavior.rotation_interval == 30
        assert len(config.contents) == 3

    def test_load_minimal_config(self, tmp_path: Path):
        """Test loading minimal configuration."""
        minimal_config = {"content": [{"source": "https://example.com"}]}
        config_file = tmp_path / "minimal.yaml"
        config_file.write_text(yaml.dump(minimal_config))

        config = load_config(str(config_file))
        assert config.display.width == 1920  # Default
        assert config.behavior.rotation_interval == 30  # Default
        assert len(config.contents) == 1

    def test_load_empty_config(self, tmp_path: Path):
        """Test loading empty configuration."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = load_config(str(config_file))
        assert config.display.screen == ":0"
        assert len(config.contents) == 0

    def test_load_config_with_urls_key(self, tmp_path: Path):
        """Test backward compatibility with 'urls' key."""
        old_config = {
            "urls": [{"type": "url", "source": "https://example.com", "duration": 10}]
        }
        config_file = tmp_path / "old.yaml"
        config_file.write_text(yaml.dump(old_config))

        config = load_config(str(config_file))
        assert len(config.contents) == 1
        assert config.contents[0].source == "https://example.com"

    def test_load_config_with_rotation(self, tmp_path: Path):
        """Test loading config with screen rotation."""
        rotated_config = {
            "display": {"rotation": "left"},
            "content": [{"source": "https://example.com"}],
        }
        config_file = tmp_path / "rotated.yaml"
        config_file.write_text(yaml.dump(rotated_config))

        config = load_config(str(config_file))
        assert config.display.rotation == "left"
