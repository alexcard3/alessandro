import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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
            with patch.object(sys, 'argv', ['daily_closed_task_review.py', '--root', str(root), '--output', str(output)]):
                with redirect_stdout(stdout):
                    exit_code = daily_review.main()

            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())
            self.assertIn(str(output), stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
