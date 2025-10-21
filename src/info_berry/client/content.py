from __future__ import annotations

import html
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, List, Literal, Optional, Tuple

ContentType = Literal["url", "html", "image", "video", "error"]


@dataclass(frozen=True)
class Content:
    id: str
    source: str
    duration: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    # Subclasses provide a class-level kind, not a dataclass field
    kind: ClassVar[ContentType] = "url"

    def to_url(self) -> str:
        raise NotImplementedError("Implement in subclasses")

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())


@dataclass(frozen=True)
class UrlContent(Content):
    kind: ClassVar[ContentType] = "url"

    def to_url(self) -> str:
        return self.source


@dataclass(frozen=True)
class HtmlFileContent(Content):
    kind: ClassVar[ContentType] = "html"

    def to_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        return f"file://{path}"


@dataclass(frozen=True)
class ImageContent(Content):
    kind: ClassVar[ContentType] = "image"

    def to_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        esc = html.escape(str(path))
        html_doc = f"""<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;height:100%;background:#000}}
img{{width:100vw;height:100vh;object-fit:contain;}}</style>
<img src="file://{esc}" />"""
        return "data:text/html;charset=utf-8," + html.escape(html_doc)


@dataclass(frozen=True)
class VideoContent(Content):
    kind: ClassVar[ContentType] = "video"

    def to_url(self) -> str:
        path = Path(self.source).expanduser().resolve()
        esc = html.escape(str(path))
        html_doc = f"""<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;height:100%;background:#000}}
video{{width:100vw;height:100vh;object-fit:contain;background:#000}}</style>
<video src="file://{esc}" autoplay muted loop playsinline controlslist="nodownload noplaybackrate" controls></video>"""
        return "data:text/html;charset=utf-8," + html.escape(html_doc)


@dataclass(frozen=True)
class ErrorContent(Content):
    kind: ClassVar[ContentType] = "error"

    def to_url(self) -> str:
        msg = html.escape(self.source or "Error")
        html_doc = f"<!doctype html><meta charset='utf-8'><body style='margin:0;background:#000;color:#f55;font:16px sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;'>Error: {msg}</body>"
        return "data:text/html;charset=utf-8," + html.escape(html_doc)


class ContentBank:
    def __init__(self, items: List[Content]):
        self._items = items[:]
        self._index = 0

    def items(self) -> List[Content]:
        return self._items

    def current(self) -> Tuple[int, Content]:
        if not self._items:
            return 0, ErrorContent(id=Content.new_id(), source="No content", duration=5)
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
