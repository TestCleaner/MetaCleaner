from __future__ import annotations

from pathlib import Path

from metacleaner.config import Config

# Xcode asset catalogs (iOS, macOS, watchOS, tvOS).
_APP_ICON_CATALOG_SUFFIXES = (".appiconset", ".launchimage")

# Directory names used across mobile and cross-platform projects.
_APP_ICON_DIR_NAMES = frozenset(
    {
        "AppIcon",
        "app_icon",
        "app-icon",
        "AppIcons",
    }
)

# Filename prefixes for launcher / store icons (Android, Flutter tooling, PWA).
_APP_ICON_FILE_PREFIXES = (
    "ic_launcher",
    "ic_launcher_foreground",
    "ic_launcher_background",
    "ic_launcher_round",
    "Icon-App-",
    "AppIcon",
    "apple-touch-icon",
    "favicon",
    "playstore-icon",
    "store_icon",
)

# Extra glob patterns for exclude_globs-style matching (Path.match).
DEFAULT_APP_ICON_GLOBS = (
    "**/*.appiconset/**",
    "**/*.launchimage/**",
    "**/mipmap-*/**",
    "**/mipmap-anydpi-v26/**",
    "**/AppIcon/**",
    "**/app_icon/**",
    "**/app-icon/**",
    "**/AppIcons/**",
    "**/ic_launcher*",
    "**/ic_launcher_foreground*",
    "**/ic_launcher_background*",
    "**/ic_launcher_round*",
    "**/Icon-App-*",
    "**/playstore-icon*",
    "**/apple-touch-icon*",
    "**/favicon*",
)


def _glob_matches(relative: Path, pattern: str) -> bool:
    if relative.match(pattern):
        return True
    if pattern.startswith("**/"):
        return relative.match(pattern[3:])
    return False


def is_app_icon_path(relative: Path) -> bool:
    """Return True when a path looks like a mobile / PWA app icon asset."""
    for part in relative.parts:
        lower = part.lower()
        if any(lower.endswith(suffix) for suffix in _APP_ICON_CATALOG_SUFFIXES):
            return True
        if part in _APP_ICON_DIR_NAMES:
            return True
        if lower.startswith("mipmap-"):
            return True

    name_lower = relative.name.lower()
    stem_lower = relative.stem.lower()
    for prefix in _APP_ICON_FILE_PREFIXES:
        prefix_lower = prefix.lower()
        if name_lower.startswith(prefix_lower) or stem_lower.startswith(prefix_lower):
            return True

    return False


def effective_exclude_globs(config: Config) -> list[str]:
    globs = list(config.exclude_globs)
    if config.skip_app_icons:
        globs.extend(DEFAULT_APP_ICON_GLOBS)
    return globs


def is_excluded_file(relative: Path, config: Config) -> bool:
    if config.skip_app_icons and is_app_icon_path(relative):
        return True

    for pattern in effective_exclude_globs(config):
        if _glob_matches(relative, pattern):
            return True
    return False
