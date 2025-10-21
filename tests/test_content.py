"""Tests for content module."""

from __future__ import annotations

import html
from pathlib import Path

import pytest

from info_berry.client.content import (
    Content,
    ContentBank,
    ErrorContent,
    HtmlFileContent,
    ImageContent,
    UrlContent,
    VideoContent,
)


class TestContent:
    """Tests for Content base class."""

    def test_new_id_generates_uuid(self):
        """Test that new_id generates valid UUID."""
        id1 = Content.new_id()
        id2 = Content.new_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID format


class TestUrlContent:
    """Tests for UrlContent."""

    def test_to_url_returns_source(self):
        """Test that to_url returns the source URL."""
        content = UrlContent(
            id=Content.new_id(), source="https://example.com", duration=10
        )
        assert content.to_url() == "https://example.com"
        assert content.kind == "url"

    def test_url_content_with_no_duration(self):
        """Test UrlContent without duration."""
        content = UrlContent(id=Content.new_id(), source="https://example.com")
        assert content.duration is None


class TestHtmlFileContent:
    """Tests for HtmlFileContent."""

    def test_to_url_returns_file_protocol(self):
        """Test that to_url returns file:// URL."""
        content = HtmlFileContent(
            id=Content.new_id(), source="/tmp/test.html", duration=10
        )
        url = content.to_url()
        assert url.startswith("file://")
        assert content.kind == "html"


class TestImageContent:
    """Tests for ImageContent."""

    def test_to_url_returns_data_uri(self):
        """Test that to_url returns data URI with HTML."""
        content = ImageContent(
            id=Content.new_id(), source="/tmp/image.png", duration=10
        )
        url = content.to_url()
        assert url.startswith("data:text/html;charset=utf-8,")
        assert content.kind == "image"

    def test_image_html_contains_img_tag(self):
        """Test that generated HTML contains img tag."""
        content = ImageContent(
            id=Content.new_id(), source="/tmp/image.png", duration=10
        )
        url = content.to_url()
        # The HTML is double-escaped: html.escape(html_doc) where html_doc contains <img>
        # So we check for the escaped version
        assert "&lt;img" in url


class TestVideoContent:
    """Tests for VideoContent."""

    def test_to_url_returns_data_uri(self):
        """Test that to_url returns data URI with HTML."""
        content = VideoContent(
            id=Content.new_id(), source="/tmp/video.mp4", duration=30
        )
        url = content.to_url()
        assert url.startswith("data:text/html;charset=utf-8,")
        assert content.kind == "video"

    def test_video_html_contains_video_tag(self):
        """Test that generated HTML contains video tag."""
        content = VideoContent(
            id=Content.new_id(), source="/tmp/video.mp4", duration=30
        )
        url = content.to_url()
        # The HTML is double-escaped
        assert "&lt;video" in url


class TestErrorContent:
    """Tests for ErrorContent."""

    def test_to_url_returns_error_message(self):
        """Test that to_url returns error HTML."""
        content = ErrorContent(
            id=Content.new_id(), source="Something went wrong", duration=5
        )
        url = content.to_url()
        assert url.startswith("data:text/html;charset=utf-8,")
        assert content.kind == "error"


class TestContentBank:
    """Tests for ContentBank."""

    def test_initialization(self):
        """Test ContentBank initialization."""
        items = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10),
            UrlContent(id=Content.new_id(), source="https://test.com", duration=20),
        ]
        bank = ContentBank(items)
        assert len(bank.items()) == 2

    def test_current_returns_first_item(self):
        """Test that current returns first item initially."""
        items = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10),
            UrlContent(id=Content.new_id(), source="https://test.com", duration=20),
        ]
        bank = ContentBank(items)
        idx, content = bank.current()
        assert idx == 0
        assert content.source == "https://example.com"

    def test_current_with_empty_bank(self):
        """Test current returns ErrorContent when empty."""
        bank = ContentBank([])
        idx, content = bank.current()
        assert idx == 0
        assert isinstance(content, ErrorContent)

    def test_next_index_cycles_through_items(self):
        """Test that next_index cycles through items."""
        items = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10),
            UrlContent(id=Content.new_id(), source="https://test.com", duration=20),
        ]
        bank = ContentBank(items)
        assert bank.next_index() == 1
        assert bank.next_index() == 0  # Cycles back

    def test_next_index_with_empty_bank(self):
        """Test next_index with empty bank."""
        bank = ContentBank([])
        assert bank.next_index() == 0

    def test_duration_for_with_content_duration(self):
        """Test duration_for returns content duration."""
        content = UrlContent(
            id=Content.new_id(), source="https://example.com", duration=10
        )
        bank = ContentBank([content])
        assert bank.duration_for(content, default_seconds=30) == 10

    def test_duration_for_with_default(self):
        """Test duration_for returns default when content has none."""
        content = UrlContent(id=Content.new_id(), source="https://example.com")
        bank = ContentBank([content])
        assert bank.duration_for(content, default_seconds=30) == 30

    def test_set_items_replaces_content(self):
        """Test set_items replaces content."""
        items1 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10)
        ]
        items2 = [
            UrlContent(id=Content.new_id(), source="https://test.com", duration=20)
        ]
        bank = ContentBank(items1)
        bank.set_items(items2)
        assert len(bank.items()) == 1
        assert bank.items()[0].source == "https://test.com"

    def test_set_items_preserves_current_index(self):
        """Test set_items preserves index when content matches."""
        items1 = [
            UrlContent(id="1", source="https://example.com", duration=10),
            UrlContent(id="2", source="https://test.com", duration=20),
        ]
        bank = ContentBank(items1)
        bank.next_index()  # Move to index 1

        items2 = [
            UrlContent(id="3", source="https://example.com", duration=10),
            UrlContent(id="4", source="https://test.com", duration=25),
        ]
        bank.set_items(items2)
        idx, content = bank.current()
        assert content.source == "https://test.com"

    def test_diff_detects_added(self):
        """Test diff detects added content."""
        items1 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10)
        ]
        items2 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10),
            UrlContent(id=Content.new_id(), source="https://new.com", duration=20),
        ]
        bank = ContentBank(items1)
        diff = bank.diff(items2)
        assert len(diff["added"]) == 1
        assert diff["added"][0] == 1

    def test_diff_detects_removed(self):
        """Test diff detects removed content."""
        items1 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10),
            UrlContent(id=Content.new_id(), source="https://old.com", duration=20),
        ]
        items2 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10)
        ]
        bank = ContentBank(items1)
        diff = bank.diff(items2)
        assert len(diff["removed"]) == 1
        assert diff["removed"][0] == 1

    def test_diff_detects_modified(self):
        """Test diff detects modified content."""
        items1 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=10)
        ]
        items2 = [
            UrlContent(id=Content.new_id(), source="https://example.com", duration=20)
        ]
        bank = ContentBank(items1)
        diff = bank.diff(items2)
        assert len(diff["modified"]) == 1
        assert diff["modified"][0] == (0, 0)
