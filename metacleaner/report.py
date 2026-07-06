from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class FileResult:
    path: str
    kind: str
    status: str
    original_bytes: int = 0
    final_bytes: int = 0
    saved_bytes: int = 0
    message: str = ""


@dataclass
class RunReport:
    project: str
    dry_run: bool
    scanned: int = 0
    processed: int = 0
    optimized: int = 0
    skipped: int = 0
    failed: int = 0
    original_total_bytes: int = 0
    final_total_bytes: int = 0
    results: list[FileResult] = field(default_factory=list)

    @property
    def saved_bytes(self) -> int:
        return max(0, self.original_total_bytes - self.final_total_bytes)

    def add(self, result: FileResult) -> None:
        self.results.append(result)
        self.scanned += 1
        if result.status == "optimized":
            self.optimized += 1
            self.processed += 1
            self.original_total_bytes += result.original_bytes
            self.final_total_bytes += result.final_bytes
        elif result.status == "skipped":
            self.skipped += 1
            self.processed += 1
            self.original_total_bytes += result.original_bytes
            self.final_total_bytes += result.original_bytes
        elif result.status == "failed":
            self.failed += 1
            self.processed += 1
        elif result.status == "dry_run":
            self.processed += 1

    def render_text(self) -> str:
        lines = [
            f"Project: {self.project}",
            f"Mode: {'dry-run' if self.dry_run else 'apply'}",
            f"Scanned: {self.scanned}",
            f"Optimized: {self.optimized}",
            f"Skipped: {self.skipped}",
            f"Failed: {self.failed}",
            f"Saved: {_format_bytes(self.saved_bytes)}",
        ]
        if self.failed:
            lines.append("")
            lines.append("Failures:")
            for item in self.results:
                if item.status == "failed":
                    lines.append(f"  - {item.path}: {item.message}")
        return "\n".join(lines)

    def render_json(self) -> str:
        payload = asdict(self)
        payload["saved_bytes"] = self.saved_bytes
        return json.dumps(payload, indent=2, ensure_ascii=False)


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"
