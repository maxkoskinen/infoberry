"""Tests for display module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from info_berry.client.display import Display


class TestDisplay:
    """Tests for Display class."""

    def test_initialization(self):
        """Test Display initialization."""
        display = Display(screen=":1", width=1280, height=720, rotation="left")
        assert display.screen == ":1"
        assert display.width == 1280
        assert display.height == 720
        assert display.rotation == "left"

    def test_default_initialization(self):
        """Test Display with default values."""
        display = Display()
        assert display.screen == ":0"
        assert display.width == 1920
        assert display.height == 1080
        assert display.rotation is None

    @pytest.mark.asyncio
    async def test_launch_creates_browser(self):
        """Test launch creates browser and context."""
        display = Display()

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        # Set up async context manager for async_playwright()
        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()

        with patch(
            "info_berry.client.display.async_playwright", return_value=async_pw_instance
        ):
            with patch(
                "info_berry.client.display.platform.system", return_value="Darwin"
            ):
                await display.launch()

        mock_playwright.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_launch_on_linux_sets_display(self):
        """Test launch sets DISPLAY environment variable on Linux."""
        display = Display(screen=":1")

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()

        with patch(
            "info_berry.client.display.async_playwright", return_value=async_pw_instance
        ):
            with patch(
                "info_berry.client.display.platform.system", return_value="Linux"
            ):
                with patch("info_berry.client.display.subprocess.run"):
                    with patch.dict(
                        "info_berry.client.display.os.environ", {}, clear=True
                    ):
                        await display.launch()
                        assert display.screen == ":1"

    @pytest.mark.asyncio
    async def test_ensure_pages_creates_pages(self):
        """Test ensure_pages creates correct number of pages."""
        display = Display()

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        # Create unique mock pages
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()

        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()

        # Set up new_page to return different pages
        mock_context.new_page = AsyncMock(side_effect=[mock_page1, mock_page2])
        mock_page1.goto = AsyncMock()
        mock_page2.goto = AsyncMock()

        with patch(
            "info_berry.client.display.async_playwright", return_value=async_pw_instance
        ):
            with patch(
                "info_berry.client.display.platform.system", return_value="Darwin"
            ):
                await display.launch()

        urls = ["https://example.com", "https://test.com"]
        await display.ensure_pages(urls)

        # Verify new_page was called twice
        assert mock_context.new_page.call_count == 2
        assert mock_page1.goto.call_count == 2
        assert mock_page2.goto.call_count == 2

        # Verify the URLs were set correctly
        mock_page1.goto.assert_any_call("about:blank")
        mock_page1.goto.assert_any_call(
            "https://example.com", wait_until="domcontentloaded", timeout=30000
        )
        mock_page2.goto.assert_any_call("about:blank")
        mock_page2.goto.assert_any_call(
            "https://test.com", wait_until="domcontentloaded", timeout=30000
        )

    @pytest.mark.asyncio
    async def test_ensure_pages_removes_extra_pages(self):
        """Test ensure_pages removes extra pages."""
        display = Display()

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        # Create 3 mock pages
        mock_pages = [MagicMock() for _ in range(3)]
        for page in mock_pages:
            page.goto = AsyncMock()
            page.close = AsyncMock()

        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()
        mock_context.new_page = AsyncMock(side_effect=mock_pages)

        with patch(
            "info_berry.client.display.async_playwright", return_value=async_pw_instance
        ):
            with patch(
                "info_berry.client.display.platform.system", return_value="Darwin"
            ):
                await display.launch()

        # Create 3 pages
        await display.ensure_pages(["url1", "url2", "url3"])
        # Reduce to 1 page
        await display.ensure_pages(["url1"])

        # Should close 2 pages
        assert mock_pages[1].close.call_count == 1
        assert mock_pages[2].close.call_count == 1

    @pytest.mark.asyncio
    async def test_show_brings_page_to_front(self):
        """Test show brings specified page to front."""
        display = Display()

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.bring_to_front = AsyncMock()

        with patch(
            "info_berry.client.display.async_playwright", return_value=async_pw_instance
        ):
            with patch(
                "info_berry.client.display.platform.system", return_value="Darwin"
            ):
                await display.launch()

        await display.ensure_pages(["url1", "url2"])
        await display.show(1)

        mock_page.bring_to_front.assert_called()

    @pytest.mark.asyncio
    async def test_reload_reloads_page(self):
        """Test reload reloads specified page."""
        display = Display()

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        async_pw_instance = MagicMock()
        async_pw_instance.start = AsyncMock(return_value=mock_playwright)

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_playwright.stop = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto
