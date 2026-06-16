#!/usr/bin/env python3
"""Generate a daily review report for consolidated/closed project tasks.

The scanner intentionally works only on closed Markdown task-list items
(`- [x] ...`) and skips any item that looks work-in-progress. This gives the
scheduled workflow a safe default: review consolidated decisions without
interfering with active development.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "reports",
    "venv",
    ".venv",
}
WIP_MARKERS = (
    "wip",
    "work in progress",
    "workingprogress",
    "working progress",
    "in progress",
    "todo",
    "doing",
)


@dataclass(frozen=True)
class ClosedTask:
    path: Path
    line: int
    text: str


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if any(part in DEFAULT_EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def is_wip(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in WIP_MARKERS)


def find_closed_tasks(root: Path) -> list[ClosedTask]:
    tasks: list[ClosedTask] = []
    for path in iter_markdown_files(root):
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            lowered = stripped.lower()
            if not (lowered.startswith("- [x]") or lowered.startswith("* [x]")):
                continue
            task_text = stripped[5:].strip()
            if is_wip(task_text):
                continue
            tasks.append(ClosedTask(path.relative_to(root), line_number, task_text))
    return tasks


def build_report(root: Path, tasks: list[ClosedTask]) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Daily closed-task review",
        "",
        f"Generated at: `{generated_at}`",
        "",
        "Scope: closed Markdown task-list items only (`- [x]`). Work-in-progress markers are ignored.",
        "",
        "## Summary",
        "",
        f"- Closed tasks reviewed: **{len(tasks)}**",
        "- Work-in-progress tasks: **skipped by design**",
        "",
    ]

    if tasks:
        lines.extend(["## Closed tasks", ""])
        for task in tasks:
            lines.append(f"- `{task.path}:{task.line}` — {task.text}")
        lines.append("")
    else:
        lines.extend([
            "## Closed tasks",
            "",
            "No consolidated Markdown task-list items were found in this checkout.",
            "",
        ])

    lines.extend([
        "## Recommended treatment",
        "",
        "For each closed task, use this review as a safe follow-up checklist:",
        "",
        "1. Confirm the closed task still matches the current implementation.",
        "2. Check whether tests or documentation should be updated after the closure.",
        "3. Look for deployment, version, or configuration drift caused by the completed work.",
        "4. Leave active or work-in-progress tasks untouched.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/daily-closed-task-review.md"),
        help="Report path, relative to root unless absolute",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    tasks = find_closed_tasks(root)
    output.write_text(build_report(root, tasks), encoding="utf-8")
    print(f"Reviewed {len(tasks)} closed task(s). Report written to {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
