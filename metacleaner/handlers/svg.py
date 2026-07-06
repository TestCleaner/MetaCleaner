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


def process_svg(source: Path, config: Config, *, dry_run: bool) -> FileResult:
    kind = "svg"
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="svg minify + metadata cleanup",
        )

    svgo = which_or_none("svgo")
    if svgo is None:
        if config.strip_metadata:
            exiftool = which_or_none("exiftool")
            if exiftool:
                result = run_command(
                    [exiftool, "-all=", "-overwrite_original", str(source)],
                    timeout=config.subprocess_timeout,
                )
                if result is not None and result.returncode == 0:
                    final_bytes = source.stat().st_size
                    if final_bytes < original_bytes:
                        return FileResult(
                            path=relative,
                            kind=kind,
                            status="optimized",
                            original_bytes=original_bytes,
                            final_bytes=final_bytes,
                            saved_bytes=original_bytes - final_bytes,
                            message="metadata stripped with exiftool",
                        )
                return FileResult(
                    path=relative,
                    kind=kind,
                    status="skipped",
                    original_bytes=original_bytes,
                    final_bytes=original_bytes,
                    message="svgo not found; no changes applied",
                )
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="svgo not found in PATH",
        )

    temp_output = temp_path_for(source)
    temp_output.unlink(missing_ok=True)

    result = run_command(
        [svgo, str(source), "-o", str(temp_output)],
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
        message="svg optimized",
    )
