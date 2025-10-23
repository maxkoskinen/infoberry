from __future__ import annotations
import html
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, List, Literal, Optional, Tuple

ContentType = Literal["url", "html", "image", "video", "error"]

@dataclass(frozen=True)
class Content:
    """Base content class with rendering logic."""
    id: str
    source: str
    duration: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    kind: ClassVar[ContentType] = "url"

    def render_url(self) -> str:
        """Return a URL or file:// path that the browser can navigate to."""
        raise NotImplementedError("Implement in subclasses")

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _generate_html_wrapper(
        body_html: str,
        title: str = "InfoBerry",
        footer: str = "Powered by InfoBerry",
    ) -> str:
        """Generate a styled HTML page with optional footer branding."""
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      height: 100%;
      background: #000;
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      overflow: hidden;
    }}
    .content {{
      width: 100vw;
      height: calc(100vh - 40px);
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .content img {{
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }}
    .content video {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .footer {{
      position: fixed;
      bottom: 0;
      width: 100%;
      height: 40px;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      color: #999;
    }}
  </style>
</head>
<body>
  <div class="content">
    {body_html}
  </div>
  <div class="footer">{html.escape(footer)}</div>
</body>
</html>
"""

    @staticmethod
    def _write_temp_html(html_content: str, prefix: str = "infoberry_") -> str:
        """Write HTML content to a temporary file and return its file:// URL."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".html",
            prefix=prefix,
            delete=False,  # Keep file so browser can load it
        ) as f:
            f.write(html_content)
            return Path(f.name).as_uri()


@dataclass(frozen=True)
class UrlContent(Content):
    """Plain HTTP(S) URL displayed directly."""
    kind: ClassVar[ContentType] = "url"

    def render_url(self) -> str:
        return self.source


@dataclass(frozen=True)
class HtmlFileContent(Content):
    """Local HTML file displayed directly."""
    kind: ClassVar[ContentType] = "html"

    def render_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        return path.as_uri()


@dataclass(frozen=True)
class ImageContent(Content):
    """Local image file wrapped in styled HTML with branding."""
    kind: ClassVar[ContentType] = "image"

    def render_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        if not path.exists():
            return ErrorContent(
                id=self.id, source=f"Image not found: {self.source}"
            ).render_url()

        img_uri = path.as_uri()
        body = f'<img src="{html.escape(img_uri)}" alt="Image">'
        html_doc = self._generate_html_wrapper(
            body_html=body,
            title=path.name,
            footer="Powered by InfoBerry · Image Display",
        )
        return self._write_temp_html(html_doc, prefix=f"img_{self.id}_")


@dataclass(frozen=True)
class VideoContent(Content):
    """Local video file wrapped in styled HTML with branding."""
    kind: ClassVar[ContentType] = "video"

    def render_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        if not path.exists():
            return ErrorContent(
                id=self.id, source=f"Video not found: {self.source}"
            ).render_url()

        vid_uri = path.as_uri()
        body = f"""<video src="{html.escape(vid_uri)}" 
                          autoplay muted loop playsinline 
                          controlslist="nodownload noplaybackrate" 
                          disablepictureinpicture></video>"""
        html_doc = self._generate_html_wrapper(
            body_html=body,
            title=path.name,
            footer="Powered by InfoBerry · Video Player",
        )
        return self._write_temp_html(html_doc, prefix=f"vid_{self.id}_")


@dataclass(frozen=True)
class ErrorContent(Content):
    """Error message displayed in styled HTML."""
    kind: ClassVar[ContentType] = "error"

    def render_url(self) -> str:
        msg = html.escape(self.source or "Unknown error")
        body = f'<pre style="color: #f66; padding: 20px;">{msg}</pre>'
        html_doc = self._generate_html_wrapper(
            body_html=body, title="Error", footer="InfoBerry Error Display"
        )
        return self._write_temp_html(html_doc, prefix="error_")


class ContentBank:
    """Manages content rotation and state."""

    def __init__(self, items: List[Content]):
        self._items = items[:]
        self._index = 0

    def items(self) -> List[Content]:
        return self._items

    def current(self) -> Tuple[int, Content]:
        if not self._items:
            return 0, ErrorContent(
                id=Content.new_id(), source="No content configured", duration=5
            )
        return self._index, self._items[self._index]

    def next_index(self) -> int:
        if not self._items:
            return 0
        self._index = (self._index + 1) % len(self._items)
        return self._index

    def set_items(self, items: List[Content]) -> None:
        old = self._items
        self._items = items[:]
        if not self._items:
            self._index = 0
            return
        try:
            cur = old[self._index]
            self._index = next(
                i
                for i, it in enumerate(self._items)
                if (it.kind, it.source) == (cur.kind, cur.source)
            )
        except Exception:
            self._index = 0

    def duration_for(self, content: Content, default_seconds: int) -> int:
        return (
            int(content.duration)
            if content.duration is not None
            else int(default_seconds)
        )

    def diff(self, new_items: List[Content]) -> dict:
        old_keys = {(it.kind, it.source): i for i, it in enumerate(self._items)}
        new_keys = {(it.kind, it.source): i for i, it in enumerate(new_items)}
        removed = [old_keys[k] for k in old_keys.keys() - new_keys.keys()]
        added = [new_keys[k] for k in new_keys.keys() - old_keys.keys()]
        modified = [
            (old_keys[k], new_keys[k])
            for k in old_keys.keys() & new_keys.keys()
            if self._items[old_keys[k]].duration != new_items[new_keys[k]].duration
        ]
        return {"removed": removed, "added": added, "modified": modified}
