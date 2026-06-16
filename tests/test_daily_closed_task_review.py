import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

TOOL_PATH = Path(__file__).resolve().parents[1] / 'tools' / 'daily_closed_task_review.py'
spec = importlib.util.spec_from_file_location('daily_closed_task_review', TOOL_PATH)
daily_review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = daily_review
spec.loader.exec_module(daily_review)


class TestDailyClosedTaskReview(unittest.TestCase):
    def test_closed_tasks_are_included_even_when_text_mentions_wip_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'TASKS.md').write_text(
                '\n'.join([
                    '- [x] Close the TODO list follow-up',
                    '- [x] Document previous work in progress decision',
                    '- [ ] Active task that should be ignored',
                ]),
                encoding='utf-8',
            )

            tasks = daily_review.find_closed_tasks(root)

            self.assertEqual(2, len(tasks))
            self.assertEqual('Close the TODO list follow-up', tasks[0].text)
            self.assertEqual('Document previous work in progress decision', tasks[1].text)

    def test_main_prints_absolute_output_path_outside_root(self):
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as output_tmp:
            root = Path(root_tmp)
            output = Path(output_tmp) / 'review.md'
            (root / 'TASKS.md').write_text('- [x] Closed task\n', encoding='utf-8')

            stdout = io.StringIO()
            argv = ['daily_closed_task_review.py', '--root', str(root), '--output', str(output)]
            with patch.object(sys, 'argv', argv):
                with redirect_stdout(stdout):
                    exit_code = daily_review.main()

            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())
            self.assertIn(str(output), stdout.getvalue())
            self.assertIn('Email summary not configured.', stdout.getvalue())

    def test_email_summary_describes_findings_and_actions(self):
        result = daily_review.ReviewResult(
            generated_at=datetime(2026, 6, 16, 6, 0, tzinfo=timezone.utc),
            closed_tasks=[daily_review.ClosedTask(Path('TASKS.md'), 12, 'Consolidated task')],
            report_path=Path('reports/daily-closed-task-review.md'),
        )

        summary = daily_review.build_email_summary(result)

        self.assertIn('Closed tasks found: 1', summary)
        self.assertIn('What it did:', summary)
        self.assertIn('TASKS.md:12', summary)
        self.assertIn('does not modify project code', summary)

    def test_email_is_skipped_when_not_configured(self):
        sent, status = daily_review.send_email_summary(
            subject='Daily review',
            body='body',
            email_to='',
            email_from='',
            smtp_host='',
            smtp_port=587,
            smtp_user='',
            smtp_password='',
            smtp_starttls=True,
        )

        self.assertFalse(sent)
        self.assertEqual('not configured', status)


if __name__ == '__main__':
    unittest.main()
