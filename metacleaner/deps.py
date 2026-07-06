from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class Dependency:
    name: str
    binaries: tuple[str, ...]
    required_for: str
    optional: bool = False


DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("mozjpeg", ("cjpeg", "djpeg", "mozjpeg"), "JPEG images"),
    Dependency("pngquant", ("pngquant",), "PNG images"),
    Dependency("cwebp", ("cwebp",), "WebP images"),
    Dependency("svgo", ("svgo",), "SVG files", optional=True),
    Dependency("ffmpeg", ("ffmpeg",), "video and HEIC files"),
    Dependency("exiftool", ("exiftool",), "metadata fallback", optional=True),
)

DEPENDENCY_BY_NAME = {dep.name: dep for dep in DEPENDENCIES}

EXTENSION_REQUIRED_TOOLS: dict[str, tuple[str, ...]] = {
    ".jpg": ("mozjpeg",),
    ".jpeg": ("mozjpeg",),
    ".png": ("pngquant",),
    ".webp": ("cwebp",),
    ".heic": ("ffmpeg",),
    ".heif": ("ffmpeg",),
    ".svg": (),
    ".mp4": ("ffmpeg",),
    ".mov": ("ffmpeg",),
    ".m4v": ("ffmpeg",),
    ".webm": ("ffmpeg",),
    ".mkv": ("ffmpeg",),
}


def find_binary(names: tuple[str, ...]) -> str | None:
    if names == ("cjpeg", "djpeg", "mozjpeg"):
        if shutil.which("cjpeg") and shutil.which("djpeg"):
            return shutil.which("cjpeg")
        return shutil.which("mozjpeg")
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def check_dependencies() -> list[tuple[Dependency, str | None]]:
    return [(dep, find_binary(dep.binaries)) for dep in DEPENDENCIES]


def missing_required_dependencies() -> list[Dependency]:
    missing: list[Dependency] = []
    for dep, path in check_dependencies():
        if dep.optional:
            continue
        if path is None:
            missing.append(dep)
    return missing


def required_tools_for_extensions(extensions: set[str]) -> set[str]:
    tools: set[str] = set()
    for ext in extensions:
        tools.update(EXTENSION_REQUIRED_TOOLS.get(ext.lower(), ()))
    return tools


def missing_dependencies_for_extensions(extensions: set[str]) -> list[Dependency]:
    missing: list[Dependency] = []
    for tool_name in sorted(required_tools_for_extensions(extensions)):
        dep = DEPENDENCY_BY_NAME[tool_name]
        if find_binary(dep.binaries) is None:
            missing.append(dep)
    return missing


def format_dependency_report() -> str:
    lines = ["Dependency check:"]
    for dep, path in check_dependencies():
        status = path if path else "missing"
        suffix = " (optional)" if dep.optional else ""
        lines.append(f"  - {dep.name}{suffix}: {status} [{dep.required_for}]")
    return "\n".join(lines)
