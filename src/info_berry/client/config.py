from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

import yaml

from .content import Content, HtmlFileContent, ImageContent, UrlContent, VideoContent


@dataclass
class BehaviorConfig:
    rotation_interval: int = 30
    refresh_interval: Optional[int] = None


@dataclass
class DisplayConfig:
    screen: str = ":0"
    width: int = 1920
    height: int = 1080
    rotation: Optional[Literal["left", "right", "inverted"]] = None


@dataclass
class AppConfig:
    display: DisplayConfig
    behavior: BehaviorConfig
    contents: List[Content]


def _to_content(obj: dict) -> Content:
    t = (obj.get("type") or "url").lower()
    src = obj["source"]
    dur = obj.get("duration")
    if t == "url":
        return UrlContent(id=Content.new_id(), source=src, duration=dur)
    if t == "html":
        return HtmlFileContent(id=Content.new_id(), source=src, duration=dur)
    if t == "image":
        return ImageContent(id=Content.new_id(), source=src, duration=dur)
    if t == "video":
        return VideoContent(id=Content.new_id(), source=src, duration=dur)
    # Default to URL if unknown
    return UrlContent(id=Content.new_id(), source=src, duration=dur)


def load_config(path: str) -> AppConfig:
    data = yaml.safe_load(Path(path).read_text()) or {}
    display = data.get("display", {}) or {}
    behavior = data.get("behavior", {}) or {}
    items = data.get("content") or data.get("urls") or []
    return AppConfig(
        display=DisplayConfig(
            screen=display.get("screen", ":0"),
            width=int(display.get("width", 1920)),
            height=int(display.get("height", 1080)),
            rotation=display.get("rotation"),
        ),
        behavior=BehaviorConfig(
            rotation_interval=int(behavior.get("rotation_interval", 30)),
            refresh_interval=behavior.get("refresh_interval"),
        ),
        contents=[_to_content(x) for x in items],
    )
