"""Tests for Git safety, repository initialization, and single-file protection."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.exceptions import GitOperationError, RepositoryConflictError
from github_activity_generator.git.operations import (
    commit_activity_change,
    prepare_activity_entry,
    push_to_remote,
)
from github_activity_generator.git.repository import initialize_local_repository
from github_activity_generator.git.safety import (
    inspect_repo_safety,
    run_git,
    validate_safe_to_operate,
)


class TestGitSafety(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.tmp.name) / "sample-repo"
        initialize_local_repository(self.repo_dir)
        run_git(["config", "user.name", "Test User"], cwd=self.repo_dir)
        run_git(["config", "user.email", "test@example.com"], cwd=self.repo_dir)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_case_7_unrelated_files_preserved(self) -> None:
        readme = self.repo_dir / "README.md"
        readme.write_text("# My Existing Project\n", encoding="utf-8")
        run_git(["add", "README.md"], cwd=self.repo_dir)
        run_git(["commit", "-m", "Initial commit"], cwd=self.repo_dir)

        activity_file = self.repo_dir / "activity.txt"
        activity_file.write_text("Custom user header\n", encoding="utf-8")
        run_git(["add", "activity.txt"], cwd=self.repo_dir)
        run_git(["commit", "-m", "Add activity.txt"], cwd=self.repo_dir)

        changed, diff = prepare_activity_entry(self.repo_dir, "Documented architecture notes")
        self.assertTrue(changed)
        self.assertIn("Documented architecture notes", diff)
        self.assertIn("Custom user header", activity_file.read_text(encoding="utf-8"))

        commit_activity_change(self.repo_dir, "Update activity log")
        # Unrelated file must remain completely untouched
        self.assertEqual(readme.read_text(encoding="utf-8"), "# My Existing Project\n")
        last_files = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=self.repo_dir)
        self.assertEqual(last_files.strip(), "activity.txt")

    def test_case_8_uncommitted_changes_detected_and_preserved(self) -> None:
        app_py = self.repo_dir / "app.py"
        app_py.write_text("print('v1')\n", encoding="utf-8")
        run_git(["add", "app.py"], cwd=self.repo_dir)
        run_git(["commit", "-m", "Add app.py"], cwd=self.repo_dir)

        # Modify unrelated file without committing
        app_py.write_text("print('wip')\n", encoding="utf-8")
        status = inspect_repo_safety(self.repo_dir)
        self.assertTrue(status.has_uncommitted_changes)
        self.assertIn("app.py", status.modified_files)

        with self.assertRaises(RepositoryConflictError):
            validate_safe_to_operate(self.repo_dir)
        # Ensure user's uncommitted work was preserved
        self.assertEqual(app_py.read_text(encoding="utf-8"), "print('wip')\n")

    def test_push_requires_confirmation_and_remote_conflict(self) -> None:
        with self.assertRaises(GitOperationError):
            push_to_remote(self.repo_dir, confirmed=False)

        dry = push_to_remote(self.repo_dir, confirmed=True, dry_run=True)
        self.assertIn("DRY RUN", dry)

        initialize_local_repository(
            self.repo_dir, remote_url="https://github.com/user/repo-a.git"
        )
        with self.assertRaises(RepositoryConflictError):
            initialize_local_repository(
                self.repo_dir, remote_url="https://github.com/user/repo-b.git"
            )


if __name__ == "__main__":
    unittest.main()
