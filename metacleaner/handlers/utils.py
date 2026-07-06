from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metacleaner.config import Config
from metacleaner.report import FileResult


def which_or_none(name: str) -> str | None:
    return shutil.which(name)


def run_command(
    args: list[str],
    *,
    timeout: int,
    dry_run: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess | None:
    if dry_run:
        return None
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=text,
        timeout=timeout,
    )


def command_error(result: subprocess.CompletedProcess | None) -> str:
    if result is None:
        return "command failed"
    stderr = result.stderr
    stdout = result.stdout
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    stderr = (stderr or "").strip()
    stdout = (stdout or "").strip()
    detail = stderr or stdout or f"exit code {result.returncode}"
    return detail[:500]


def finalize_output(
    *,
    source: Path,
    temp_output: Path,
    kind: str,
    config: Config,
    dry_run: bool,
    message: str,
) -> FileResult:
    relative = str(source)
    original_bytes = source.stat().st_size

    if dry_run:
        return FileResult(
            path=relative,
            kind=kind,
            status="dry_run",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message=message or "would process",
        )

    if not temp_output.exists():
        return FileResult(
            path=relative,
            kind=kind,
            status="failed",
            original_bytes=original_bytes,
            message="temporary output was not created",
        )

    final_bytes = temp_output.stat().st_size
    if config.skip_if_larger and final_bytes >= original_bytes:
        temp_output.unlink(missing_ok=True)
        return FileResult(
            path=relative,
            kind=kind,
            status="skipped",
            original_bytes=original_bytes,
            final_bytes=original_bytes,
            message="optimized file is not smaller",
        )

    temp_output.replace(source)
    return FileResult(
        path=relative,
        kind=kind,
        status="optimized",
        original_bytes=original_bytes,
        final_bytes=final_bytes,
        saved_bytes=original_bytes - final_bytes,
        message=message,
    )


def temp_path_for(source: Path) -> Path:
    # Keep the real media extension at the end so FFmpeg and other tools can detect format.
    return source.with_name(f"{source.stem}.metacleaner.tmp{source.suffix}")
