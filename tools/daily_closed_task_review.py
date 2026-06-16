#!/usr/bin/env python3
"""Generate a daily review report for consolidated/closed project tasks.

The scanner works on closed Markdown task-list items (`- [x] ...`), which are
consolidated by definition. Active items (`- [ ]`) are not matched, so the
scheduled workflow reviews completed decisions without touching live work.
"""
from __future__ import annotations

import argparse
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
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
DEFAULT_REPORT_PATH = Path("reports/daily-closed-task-review.md")
DEFAULT_TASKS_PATH = Path("TASKS.md")


@dataclass(frozen=True)
class ClosedTask:
    path: Path
    line: int
    text: str


@dataclass(frozen=True)
class ReviewResult:
    generated_at: datetime
    closed_tasks: list[ClosedTask]
    report_path: Path
    email_sent: bool = False
    email_status: str = "not configured"


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if any(part in DEFAULT_EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


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
            tasks.append(ClosedTask(path.relative_to(root), line_number, task_text))
    return tasks


def display_path(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def build_email_summary(result: ReviewResult) -> str:
    lines = [
        "Daily closed-task review completed.",
        "",
        f"Generated at: {result.generated_at.isoformat(timespec='seconds')}",
        f"Closed tasks found: {len(result.closed_tasks)}",
        f"Report: {result.report_path}",
        "",
        "What it did:",
        "- Scanned Markdown task lists for closed items only (`- [x]` / `* [x]`).",
        "- Left active unchecked tasks untouched.",
        "- Wrote the full Markdown report.",
        "",
    ]

    if result.closed_tasks:
        lines.append("Top closed items:")
        for task in result.closed_tasks[:10]:
            lines.append(f"- {task.path}:{task.line} — {task.text}")
        if len(result.closed_tasks) > 10:
            lines.append(f"- ...and {len(result.closed_tasks) - 10} more item(s).")
    else:
        lines.append("No closed Markdown task-list items were found.")

    lines.extend([
        "",
        "Recommended next action:",
        "- Review the artifact/report only; this automation does not modify project code.",
    ])
    return "\n".join(lines)


def build_report(result: ReviewResult) -> str:
    lines = [
        "# Daily closed-task review",
        "",
        f"Generated at: `{result.generated_at.isoformat(timespec='seconds')}`",
        "",
        "Scope: closed Markdown task-list items only (`- [x]`). Active items (`- [ ]`) are ignored.",
        "",
        "## Summary",
        "",
        f"- Closed tasks reviewed: **{len(result.closed_tasks)}**",
        "- Active tasks: **skipped by design**",
        f"- Email summary: **{result.email_status}**",
        "- Repository changes made by this automation: **none**",
        "",
    ]

    if result.closed_tasks:
        lines.extend(["## Closed tasks", ""])
        for task in result.closed_tasks:
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
        "4. Leave active tasks untouched.",
        "",
    ])
    return "\n".join(lines)


def send_email_summary(
    *,
    subject: str,
    body: str,
    email_to: str | None,
    email_from: str | None,
    smtp_host: str | None,
    smtp_port: int,
    smtp_user: str | None,
    smtp_password: str | None,
    smtp_starttls: bool,
) -> tuple[bool, str]:
    if not (email_to and email_from and smtp_host):
        return False, "not configured"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        if smtp_starttls:
            smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)
    return True, f"sent to {email_to}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Report path, relative to root unless absolute",
    )
    parser.add_argument("--email-to", default=None, help="Optional summary email recipient")
    parser.add_argument("--email-from", default=None, help="Optional summary email sender")
    parser.add_argument("--email-subject", default="Daily closed-task review", help="Summary email subject")
    parser.add_argument("--smtp-host", default=None, help="SMTP host for optional summary email")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP port for optional summary email")
    parser.add_argument("--smtp-user", default=None, help="SMTP username for optional summary email")
    parser.add_argument("--smtp-password", default=None, help="SMTP password for optional summary email")
    parser.add_argument(
        "--smtp-no-starttls",
        action="store_true",
        help="Disable STARTTLS for optional summary email",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    result = ReviewResult(
        generated_at=datetime.now(timezone.utc),
        closed_tasks=find_closed_tasks(root),
        report_path=display_path(output, root),
    )
    email_sent, email_status = send_email_summary(
        subject=args.email_subject,
        body=build_email_summary(result),
        email_to=args.email_to,
        email_from=args.email_from,
        smtp_host=args.smtp_host,
        smtp_port=args.smtp_port,
        smtp_user=args.smtp_user,
        smtp_password=args.smtp_password,
        smtp_starttls=not args.smtp_no_starttls,
    )
    result = ReviewResult(
        generated_at=result.generated_at,
        closed_tasks=result.closed_tasks,
        report_path=result.report_path,
        email_sent=email_sent,
        email_status=email_status,
    )

    output.write_text(build_report(result), encoding="utf-8")
    print(f"Reviewed {len(result.closed_tasks)} closed task(s). Report written to {result.report_path}")
    print(f"Email summary {result.email_status}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
