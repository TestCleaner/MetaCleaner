from __future__ import annotations

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


def _video_encode_args(source: Path, config: Config) -> tuple[list[str], str]:
    ext = source.suffix.lower()

    if ext == ".webm":
        # WebM only supports VP8/VP9/AV1 — not H.264.
        vp9_crf = min(63, config.video_crf + 8)
        return (
            [
                "-c:v",
                "libvpx-vp9",
                "-crf",
                str(vp9_crf),
                "-b:v",
                "0",
                "-row-mt",
                "1",
                "-cpu-used",
                str(config.video_webm_cpu_used),
                "-c:a",
                "copy",
            ],
            "vp9",
        )

    if ext in {".mp4", ".m4v", ".mov"}:
        return (
            [
                "-c:v",
                "libx264",
                "-crf",
                str(config.video_crf),
                "-preset",
                config.video_preset,
                "-movflags",
                "+faststart",
                "-c:a",
                "copy",
            ],
            "h264",
        )

    # .mkv and other containers
    return (
        [
            "-c:v",
            "libx264",
            "-crf",
            str(config.video_crf),
            "-preset",
            config.video_preset,
            "-c:a",
            "copy",
        ],
        "h264",
    )


def process_video(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "video"
    relative = str(source)
    original_bytes = source.stat().st_size
    _, codec_label = _video_encode_args(source, config)

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message=f"video metadata strip + {codec_label} compress",
        )

    ffmpeg = which_or_none("ffmpeg")
    if ffmpeg is None:
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="ffmpeg not found in PATH",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)

    encode_args, _ = _video_encode_args(source, config)
    args = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        *encode_args,
    ]
    if config.strip_metadata:
        args.extend(["-map_metadata", "-1", "-map_chapters", "-1"])
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
        message=f"video optimized ({codec_label})",
    )
