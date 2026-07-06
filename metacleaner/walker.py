from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path

from metacleaner.config import Config


@dataclass(frozen=True)
class MediaFile:
    path: Path
    relative: Path
    kind: str


def _is_excluded_file(relative: Path, exclude_globs: list[str]) -> bool:
    relative_posix = relative.as_posix()
    for pattern in exclude_globs:
        if fnmatch.fnmatch(relative_posix, pattern):
            return True
    return False


def walk_media_files(project_root: Path, config: Config, *, images_only: bool = False, videos_only: bool = False) -> list[MediaFile]:
    project_root = project_root.resolve()
    allowed = _allowed_extensions(config, images_only=images_only, videos_only=videos_only)
    found: list[MediaFile] = []

    def scan(directory: Path) -> None:
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    name = entry.name
                    if name.startswith(".") and name not in {".", ".."}:
                        # Still allow dotfiles if they are media, but skip hidden dirs like .git
                        if entry.is_dir(follow_symlinks=False) and name in config.exclude_dirs:
                            continue
                    path = Path(entry.path)

                    if entry.is_dir(follow_symlinks=False):
                        if name in config.exclude_dirs:
                            continue
                        scan(path)
                        continue

                    if not entry.is_file(follow_symlinks=False):
                        continue

                    suffix = path.suffix.lower()
                    if suffix not in allowed:
                        continue

                    relative = path.relative_to(project_root)
                    if _is_excluded_file(relative, config.exclude_globs):
                        continue

                    kind = config.media_kind(suffix)
                    if kind is None:
                        continue

                    found.append(MediaFile(path=path, relative=relative, kind=kind))
        except OSError:
            return

    scan(project_root)
    found.sort(key=lambda item: item.relative.as_posix())
    return found


def _allowed_extensions(config: Config, *, images_only: bool, videos_only: bool) -> set[str]:
    if images_only:
        return set(config.extensions_images | config.extensions_svg)
    if videos_only:
        return set(config.extensions_videos)
    return set(config.all_extensions)


def resolve_media_files(
    project_root: Path,
    config: Config,
    paths: list[Path],
    *,
    images_only: bool = False,
    videos_only: bool = False,
) -> list[MediaFile]:
    project_root = project_root.resolve()
    allowed = _allowed_extensions(config, images_only=images_only, videos_only=videos_only)
    found: list[MediaFile] = []

    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else (project_root / raw_path)
        path = path.resolve()

        if not path.is_file():
            continue

        try:
            relative = path.relative_to(project_root)
        except ValueError:
            relative = path

        suffix = path.suffix.lower()
        if suffix not in allowed:
            continue

        if _is_excluded_file(relative, config.exclude_globs):
            continue

        kind = config.media_kind(suffix)
        if kind is None:
            continue

        found.append(MediaFile(path=path, relative=relative, kind=kind))

    found.sort(key=lambda item: item.relative.as_posix())
    return found
