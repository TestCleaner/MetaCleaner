from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from metacleaner.config import load_config
from metacleaner.deps import (
    format_dependency_report,
    missing_dependencies_for_extensions,
    missing_required_dependencies,
)
from metacleaner.handlers import process_image, process_svg, process_video
from metacleaner.report import FileResult, RunReport
from metacleaner.walker import MediaFile, resolve_media_files, walk_media_files


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metacleaner",
        description="Strip metadata and optimize media files in a project directory.",
    )
    parser.add_argument("project", type=Path, help="Path to the project directory")
    parser.add_argument("--config", type=Path, default=None, help="Path to metacleaner config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Scan and report without modifying files")
    parser.add_argument("--check", action="store_true", help="Exit 1 if any file could be optimized")
    parser.add_argument("--doctor", action="store_true", help="Check external tool dependencies")
    parser.add_argument("--json", action="store_true", help="Print report as JSON")
    parser.add_argument("--verbose", action="store_true", help="Print per-file progress")
    parser.add_argument("--images-only", action="store_true", help="Process only images and SVG")
    parser.add_argument("--videos-only", action="store_true", help="Process only videos")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="Parallel workers (default: 4)")
    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="Process only these files (paths relative to project root)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any file failed (default: fail only when nothing was optimized)",
    )
    return parser


def _process_file(media: MediaFile, config, *, dry_run: bool) -> FileResult:
    if media.kind == "image":
        return process_image(media.path, config, dry_run=dry_run)
    if media.kind == "svg":
        return process_svg(media.path, config, dry_run=dry_run)
    if media.kind == "video":
        return process_video(media.path, config, dry_run=dry_run)
    return FileResult(
        path=str(media.path),
        kind=media.kind,
        status="failed",
        message=f"unsupported media kind: {media.kind}",
    )


def _run(project: Path, args: argparse.Namespace) -> int:
    project_root = project.resolve()
    if not project_root.is_dir():
        print(f"Error: not a directory: {project_root}", file=sys.stderr)
        return 2

    if args.doctor:
        print(format_dependency_report())
        return 1 if missing_required_dependencies() else 0

    config = load_config(project_root, args.config)

    if args.images_only and args.videos_only:
        print("Error: --images-only and --videos-only cannot be used together", file=sys.stderr)
        return 2

    if args.files:
        media_files = resolve_media_files(
            project_root,
            config,
            args.files,
            images_only=args.images_only,
            videos_only=args.videos_only,
        )
    else:
        media_files = walk_media_files(
            project_root,
            config,
            images_only=args.images_only,
            videos_only=args.videos_only,
        )

    found_extensions = {media.path.suffix.lower() for media in media_files}
    missing = missing_dependencies_for_extensions(found_extensions)
    if missing and not args.dry_run and not args.check:
        names = ", ".join(dep.name for dep in missing)
        print(f"Error: missing required tools: {names}", file=sys.stderr)
        print("Run with --doctor for details.", file=sys.stderr)
        return 2

    report = RunReport(project=str(project_root), dry_run=args.dry_run or args.check)
    if not media_files:
        if args.json:
            print(report.render_json())
        else:
            print(report.render_text())
            print("\nNo media files found.")
        return 0

    jobs = max(1, args.jobs)
    dry_run = args.dry_run or args.check

    if jobs == 1:
        for media in media_files:
            result = _process_file(media, config, dry_run=dry_run)
            report.add(result)
            if args.verbose:
                print(f"[{result.status}] {result.path}")
    else:
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            futures = {
                executor.submit(_process_file, media, config, dry_run=dry_run): media
                for media in media_files
            }
            for future in as_completed(futures):
                result = future.result()
                report.add(result)
                if args.verbose:
                    print(f"[{result.status}] {result.path}")

    if args.json:
        print(report.render_json())
    else:
        print(report.render_text())

    if args.check:
        return 1 if report.scanned > 0 else 0

    if report.failed:
        if args.strict:
            return 1
        if report.optimized == 0:
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return _run(args.project, args)


if __name__ == "__main__":
    raise SystemExit(main())
