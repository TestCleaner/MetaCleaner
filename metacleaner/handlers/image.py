from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

from metacleaner.config import Config
from metacleaner.handlers.utils import (
    command_error,
    finalize_output,
    run_command,
    temp_path_for,
    which_or_none,
)
from metacleaner.report import FileResult


def _jpeg_binary(name: str) -> str | None:
    for candidate in (name,):
        path = which_or_none(candidate)
        if path:
            return path
    if name == "cjpeg":
        return which_or_none("mozjpeg")
    return None


def process_jpeg(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "image"
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="jpeg optimize + strip metadata",
        )

    cjpeg = _jpeg_binary("cjpeg")
    djpeg = _jpeg_binary("djpeg")
    if cjpeg is None or djpeg is None:
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="djpeg/cjpeg (mozjpeg) not found in PATH",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)

    decode = run_command(
        [djpeg, str(source)],
        timeout=config.subprocess_timeout,
        text=False,
    )
    if decode is None or decode.returncode != 0:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message=command_error(decode),
        )

    encode = subprocess.run(
        [
            cjpeg,
            "-quality",
            str(config.jpeg_quality),
            "-optimize",
            "-progressive",
            "-outfile",
            str(temp_output),
        ],
        input=decode.stdout,
        capture_output=True,
        check=False,
        timeout=config.subprocess_timeout,
    )
    if encode.returncode != 0:
        temp_output.unlink(missing_ok=True)
        stderr = (encode.stderr or b"").decode("utf-8", errors="replace").strip()
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message=stderr or f"exit code {encode.returncode}",
        )

    return finalize_output(
        source=source,
        temp_output=temp_output,
        kind=kind,
        config=config,
        dry_run=dry_run,
        message="jpeg optimized",
    )


def process_png(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "image"
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        mode = "lossless oxipng" if config.png_lossless else "pngquant high-quality"
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message=f"png optimize ({mode}) + strip metadata",
        )

    if config.png_lossless:
        return _process_png_lossless(source, config, dry_run=dry_run)

    pngquant = which_or_none("pngquant")
    if pngquant is None:
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="pngquant not found in PATH",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)

    args = [
        pngquant,
        "--quality",
        config.png_quality,
        "--speed",
        str(config.png_speed),
        "--output",
        str(temp_output),
        "--force",
        str(source),
    ]
    if config.strip_metadata:
        args.insert(1, "--strip")

    result = run_command(args, timeout=config.subprocess_timeout)
    if result is None:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="pngquant did not run",
        )

    # Exit 99: cannot meet minimum quality — fall back to lossless instead of skipping.
    if result.returncode == 99:
        temp_output.unlink(missing_ok=True)
        fallback = _process_png_lossless(source, config, dry_run=dry_run)
        if fallback.status != "failed":
            return fallback
        return FileResult(
            path=relative,
            kind=kind,
            status="skipped",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="pngquant quality threshold not met; lossless fallback unavailable",
        )

    if result.returncode != 0:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message=command_error(result),
        )

    return finalize_output(
        source=source,
        temp_output=temp_output,
        kind=kind,
        config=config,
        dry_run=dry_run,
        message="png optimized",
    )


def _process_png_lossless(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "image"
    relative = str(source)
    original_bytes = source.stat().st_size

    oxipng = which_or_none("oxipng")
    if oxipng is None:
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="oxipng not found in PATH (install for lossless PNG mode)",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)
    shutil.copy2(source, temp_output)

    args = [oxipng, "-o", "2"]
    if config.strip_metadata:
        args.extend(["--strip", "safe"])
    args.append(str(temp_output))

    result = run_command(args, timeout=config.subprocess_timeout)
    if result is None or result.returncode != 0:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message=command_error(result),
        )

    return finalize_output(
        source=source,
        temp_output=temp_output,
        kind=kind,
        config=config,
        dry_run=dry_run,
        message="png lossless optimized",
    )


def process_webp(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "image"
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="webp optimize + strip metadata",
        )

    cwebp = which_or_none("cwebp")
    if cwebp is None:
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="cwebp not found in PATH",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)

    result = run_command(
        [
            cwebp,
            "-q",
            str(config.webp_quality),
            "-metadata",
            "none",
            "-o",
            str(temp_output),
            str(source),
        ],
        timeout=config.subprocess_timeout,
    )
    if result is None or result.returncode != 0:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message=command_error(result),
        )

    return finalize_output(
        source=source,
        temp_output=temp_output,
        kind=kind,
        config=config,
        dry_run=dry_run,
        message="webp optimized",
    )


def _heic_strip_metadata_only(source: Path, config: Config, original_bytes: int) -> FileResult | None:
    kind = "image"
    relative = str(source)
    exiftool = which_or_none("exiftool")
    if not exiftool or not config.strip_metadata:
        return None
    result = run_command(
        [exiftool, "-all=", "-overwrite_original", str(source)],
        timeout=config.subprocess_timeout,
    )
    if result is None or result.returncode != 0:
        return None
    final_bytes = source.stat().st_size
    if final_bytes < original_bytes:
        return FileResult(
            path=relative,
            kind=kind,
            status="optimized",
            original_bytes=original_bytes,
            final_bytes=final_bytes,
            saved_bytes=original_bytes - final_bytes,
            message="metadata stripped only",
        )
    return FileResult(
        path=relative,
        kind=kind,
        status="skipped",
        original_bytes=original_bytes,
        final_bytes=original_bytes,
        message="metadata stripped; size unchanged",
    )


def _heic_convert_with_heif_convert(source: Path, temp_output: Path, config: Config) -> bool:
    heif_convert = which_or_none("heif-convert")
    if heif_convert is None:
        return False
    result = run_command(
        [heif_convert, str(source), str(temp_output)],
        timeout=config.subprocess_timeout,
    )
    return result is not None and result.returncode == 0 and temp_output.exists()


def _heic_convert_with_ffmpeg(source: Path, temp_output: Path, config: Config) -> bool:
    ffmpeg = which_or_none("ffmpeg")
    if ffmpeg is None:
        return False
    args = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-q:v",
        str(max(2, min(31, 31 - config.jpeg_quality // 3))),
        "-c:v",
        "mjpeg",
    ]
    if config.strip_metadata:
        args.extend(["-map_metadata", "-1"])
    args.append(str(temp_output))
    result = run_command(args, timeout=config.subprocess_timeout)
    return result is not None and result.returncode == 0 and temp_output.exists()


def process_heic(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "image"
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="heic metadata strip + convert to jpeg",
        )

    jpeg_target = source.with_suffix(".jpg")
    temp_output = temp_path_for(jpeg_target)
    temp_output.unlink(missing_ok=True)

    converted = _heic_convert_with_heif_convert(source, temp_output, config)
    if not converted:
        converted = _heic_convert_with_ffmpeg(source, temp_output, config)

    if not converted:
        temp_output.unlink(missing_ok=True)
        metadata_only = _heic_strip_metadata_only(source, config, original_bytes)
        if metadata_only is not None:
            return metadata_only
        return FileResult(
            path=relative,
            kind=kind,
            status="skipped",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="heic unreadable or corrupt; left unchanged",
        )

    if config.skip_if_larger and temp_output.stat().st_size >= original_bytes:
        temp_output.unlink(missing_ok=True)
        metadata_only = _heic_strip_metadata_only(source, config, original_bytes)
        if metadata_only is not None:
            return metadata_only
        return FileResult(
            path=relative,
            kind=kind,
            status="skipped",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="jpeg conversion is not smaller",
        )

    if source.exists() and jpeg_target != source:
        source.unlink()
    temp_output.replace(jpeg_target)
    final_bytes = jpeg_target.stat().st_size
    return FileResult(
        path=relative,
        kind=kind,
        status="optimized",
        original_bytes=original_bytes,
        final_bytes=final_bytes,
        saved_bytes=original_bytes - final_bytes,
        message="converted heic to jpeg",
    )


def process_image(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    suffix = source.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return process_jpeg(source, config, dry_run=dry_run)
    if suffix == ".png":
        return process_png(source, config, dry_run=dry_run)
    if suffix == ".webp":
        return process_webp(source, config, dry_run=dry_run)
    if suffix in {".heic", ".heif"}:
        return process_heic(source, config, dry_run=dry_run)

    return FileResult(
        path=str(source),
        kind="image",
        status="failed",
        message=f"unsupported image format: {suffix}",
    )
