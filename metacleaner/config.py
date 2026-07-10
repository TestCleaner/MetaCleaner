from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "build",
        "dist",
        "out",
        ".dart_tool",
        "Pods",
        "DerivedData",
        ".gradle",
        "vendor",
        "__pycache__",
        ".idea",
        ".vscode",
        "Carthage",
    }
)

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"})
SVG_EXTENSIONS = frozenset({".svg"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".webm", ".mkv"})

@dataclass
class Config:
    jpeg_quality: int = 85
    png_quality: str = "92-100"
    png_speed: int = 1
    png_lossless: bool = False
    webp_quality: int = 80
    video_crf: int = 24
    video_preset: str = "fast"
    video_webm_cpu_used: int = 2
    strip_metadata: bool = True
    skip_if_larger: bool = True
    skip_app_icons: bool = True
    exclude_dirs: set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDE_DIRS))
    exclude_globs: list[str] = field(default_factory=list)
    extensions_images: set[str] = field(default_factory=lambda: set(IMAGE_EXTENSIONS))
    extensions_svg: set[str] = field(default_factory=lambda: set(SVG_EXTENSIONS))
    extensions_videos: set[str] = field(default_factory=lambda: set(VIDEO_EXTENSIONS))
    subprocess_timeout: int = 300

    @property
    def all_extensions(self) -> frozenset[str]:
        return frozenset(self.extensions_images | self.extensions_svg | self.extensions_videos)

    def media_kind(self, suffix: str) -> str | None:
        lower = suffix.lower()
        if lower in self.extensions_images:
            return "image"
        if lower in self.extensions_svg:
            return "svg"
        if lower in self.extensions_videos:
            return "video"
        return None


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_config(project_root: Path, config_path: Path | None = None) -> Config:
    defaults: dict[str, Any] = {
        "jpeg_quality": 85,
        "png_quality": "92-100",
        "png_speed": 1,
        "png_lossless": False,
        "webp_quality": 80,
        "video_crf": 24,
        "video_preset": "fast",
        "video_webm_cpu_used": 2,
        "strip_metadata": True,
        "skip_if_larger": True,
        "skip_app_icons": True,
        "subprocess_timeout": 300,
        "exclude_dirs": sorted(DEFAULT_EXCLUDE_DIRS),
        "exclude_globs": [],
        "extensions": {
            "images": sorted(IMAGE_EXTENSIONS),
            "svg": sorted(SVG_EXTENSIONS),
            "videos": sorted(VIDEO_EXTENSIONS),
        },
    }

    candidates: list[Path] = []
    if config_path is not None:
        candidates.append(config_path)
    else:
        candidates.extend(
            [
                project_root / ".metacleaner.yaml",
                project_root / "metacleaner.yaml",
            ]
        )

    data = dict(defaults)
    for candidate in candidates:
        if candidate.is_file():
            with candidate.open(encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
            data = _merge_dict(data, loaded)
            break

    exclude_dirs = set(data.get("exclude_dirs") or DEFAULT_EXCLUDE_DIRS)
    extensions = data.get("extensions") or {}

    return Config(
        jpeg_quality=int(data.get("jpeg_quality", 85)),
        png_quality=str(data.get("png_quality", "92-100")),
        png_speed=max(1, min(11, int(data.get("png_speed", 1)))),
        png_lossless=bool(data.get("png_lossless", False)),
        webp_quality=int(data.get("webp_quality", 80)),
        video_crf=int(data.get("video_crf", 24)),
        video_preset=str(data.get("video_preset", "fast")),
        video_webm_cpu_used=max(0, min(5, int(data.get("video_webm_cpu_used", 2)))),
        strip_metadata=bool(data.get("strip_metadata", True)),
        skip_if_larger=bool(data.get("skip_if_larger", True)),
        skip_app_icons=bool(data.get("skip_app_icons", True)),
        exclude_dirs=exclude_dirs,
        exclude_globs=list(data.get("exclude_globs") or []),
        extensions_images={ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions.get("images", IMAGE_EXTENSIONS)},
        extensions_svg={ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions.get("svg", SVG_EXTENSIONS)},
        extensions_videos={ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions.get("videos", VIDEO_EXTENSIONS)},
        subprocess_timeout=int(data.get("subprocess_timeout", 300)),
    )
