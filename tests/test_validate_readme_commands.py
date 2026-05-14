import io
import subprocess
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from validate_readme_commands import (
    DEFAULT_LABS,
    CommandExecutionError,
    CommandSpec,
    _expected_output_matches,
    derive_final_cleanup_commands,
    main,
    parse_readme_commands,
    print_command_mapping,
    reset_lab_changes,
    resolve_readme_paths,
    run_single_readme,
    run_cleanup_commands,
    run_command_specs,
    snapshot_repo_state,
    should_skip_command,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class GitRepoTestCase(unittest.TestCase):
    def _init_git_repo(self, repo_path: Path) -> None:
        self._git(repo_path, "init")
        self._git(repo_path, "config", "user.name", "Test User")
        self._git(repo_path, "config", "user.email", "test@example.com")

    def _git(self, cwd: Path, *args: str) -> None:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)


class ParseReadmeCommandsTests(GitRepoTestCase):
    def test_collects_terminaloutput_blocks_until_next_shell_block(self) -> None:
        readme_path = self._write_readme(
            """
            Intro

            ```shell
            echo first
            ```

            prose between blocks

            ```terminaloutput
            first
            ```

            ```terminaloutput
            second
            ```

            ```shell
            echo third
            ```
            """
        )

        commands = parse_readme_commands(readme_path)

        self.assertEqual(
            commands,
            [
                CommandSpec(
                    command="echo first\n",
                    expected_outputs=["first\n", "second\n"],
                ),
                CommandSpec(command="echo third\n", expected_outputs=[]),
            ],
        )

    def test_ignores_terminaloutput_before_first_shell_block(self) -> None:
        readme_path = self._write_readme(
            """
            ```terminaloutput
            orphan
            ```

            ```shell
            echo ok
            ```
            """
        )

        commands = parse_readme_commands(readme_path)

        self.assertEqual(commands, [CommandSpec(command="echo ok\n", expected_outputs=[])])

    def test_repo_readme_parses_with_expected_shape(self) -> None:
        commands = parse_readme_commands(ROOT_DIR / "api-coverage" / "README.md")

        self.assertEqual(len(commands), 7)
        self.assertEqual(
            commands[0].command,
            "docker compose up test --build --abort-on-container-exit\n",
        )
        self.assertEqual(len(commands[0].expected_outputs), 3)
        self.assertEqual(commands[1].command, "docker compose down -v\n")
        self.assertEqual(commands[1].expected_outputs, [])

    def _write_readme(self, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        readme_path = Path(temp_dir.name) / "README.md"
        readme_path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return readme_path


class RunCommandSpecsTests(GitRepoTestCase):
    def test_zero_exit_with_matching_output_passes(self) -> None:
        results = run_command_specs(
            [CommandSpec(command="printf 'hello\\n'", expected_outputs=["hello\n"])],
            cwd=ROOT_DIR,
            timeout_seconds=5,
        )

        self.assertEqual(len(results.results), 1)
        self.assertEqual(results.results[0].returncode, 0)

    def test_non_zero_exit_with_matching_output_passes(self) -> None:
        results = run_command_specs(
            [CommandSpec(command="printf 'expected\\n'; exit 3", expected_outputs=["expected\n"])],
            cwd=ROOT_DIR,
            timeout_seconds=5,
        )

        self.assertEqual(len(results.results), 1)
        self.assertFalse(results.results[0].skipped)
        self.assertEqual(results.results[0].returncode, 3)

    def test_non_zero_exit_without_expected_output_fails(self) -> None:
        with self.assertRaises(CommandExecutionError) as ctx:
            run_command_specs(
                [CommandSpec(command="printf 'wrong\\n'; exit 4", expected_outputs=["expected\n"])],
                cwd=ROOT_DIR,
                timeout_seconds=5,
            )

        self.assertIn("missing expected terminaloutput block #1", str(ctx.exception))
        self.assertIn("Exit code: 4", str(ctx.exception))

    def test_non_zero_exit_without_terminaloutput_blocks_fails(self) -> None:
        with self.assertRaises(CommandExecutionError) as ctx:
            run_command_specs(
                [CommandSpec(command="exit 7", expected_outputs=[])],
                cwd=ROOT_DIR,
                timeout_seconds=5,
            )

        self.assertIn("command exited non-zero without any expected terminaloutput blocks", str(ctx.exception))

    def test_line_by_line_matching_allows_prefixed_actual_lines(self) -> None:
        expected_output = (
            "Failed the following API Coverage Report success criteria:\n"
            "Total API coverage: 50% is less than the specified minimum threshold of 100%.\n"
            "Total missed operations: 1 is greater than the maximum threshold of 0.\n"
        )
        actual_output = (
            "api-coverage-openapi-test  | Failed the following API Coverage Report success criteria:\n"
            "api-coverage-openapi-test  | Total API coverage: 50% is less than the specified minimum threshold of 100%.\n"
            "api-coverage-openapi-test  | Total missed operations: 1 is greater than the maximum threshold of 0.\n"
        )

        self.assertTrue(_expected_output_matches(expected_output, actual_output))

    def test_line_by_line_matching_preserves_order(self) -> None:
        expected_output = "first line\nsecond line\n"
        actual_output = "prefix second line\nprefix first line\n"

        self.assertFalse(_expected_output_matches(expected_output, actual_output))

    def test_timeout_is_reported_cleanly(self) -> None:
        with self.assertRaises(CommandExecutionError) as ctx:
            run_command_specs(
                [CommandSpec(command="sleep 2", expected_outputs=[])],
                cwd=ROOT_DIR,
                timeout_seconds=0.1,
            )

        self.assertIn("timed out after 0.1 seconds", str(ctx.exception))

    def test_streams_command_output_in_realtime_to_terminal(self) -> None:
        stdout_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer), redirect_stderr(io.StringIO()):
            results = run_command_specs(
                [CommandSpec(command="printf 'streamed\\n'", expected_outputs=["streamed\n"])],
                cwd=ROOT_DIR,
                timeout_seconds=5,
            )

        self.assertEqual(len(results.results), 1)
        self.assertIn("streamed\n", stdout_buffer.getvalue())

    def test_skips_commands_containing_docker_and_studio(self) -> None:
        results = run_command_specs(
            [
                CommandSpec(
                    command="docker compose --profile studio up --build",
                    expected_outputs=[],
                )
            ],
            cwd=ROOT_DIR,
            timeout_seconds=5,
        )

        self.assertEqual(len(results.results), 1)
        self.assertTrue(results.results[0].skipped)
        self.assertEqual(results.results[0].returncode, 0)

    def test_runs_cleanup_commands_after_failure_but_skips_non_cleanup_zero_output_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cleanup_marker = temp_path / "cleanup.txt"
            non_cleanup_marker = temp_path / "non_cleanup.txt"
            stderr_buffer = io.StringIO()

            with redirect_stderr(stderr_buffer):
                with self.assertRaises(CommandExecutionError) as ctx:
                    run_command_specs(
                        [
                            CommandSpec(command="printf 'actual\\n'", expected_outputs=["expected\n"]),
                            CommandSpec(
                                command=f"kill -0 $$ >/dev/null 2>&1; printf cleanup > {cleanup_marker.name}",
                                expected_outputs=[],
                            ),
                            CommandSpec(command=f"printf mutate > {non_cleanup_marker.name}", expected_outputs=[]),
                            CommandSpec(command="printf 'later\\n'", expected_outputs=["later\n"]),
                        ],
                        cwd=temp_path,
                        timeout_seconds=5,
                    )

            self.assertIn("Cleanup commands executed", str(ctx.exception))
            self.assertIn(
                "Validation failed at command #1. Skipping remaining commands and running cleanup commands...",
                stderr_buffer.getvalue(),
            )
            self.assertTrue(cleanup_marker.exists())
            self.assertFalse(non_cleanup_marker.exists())


class CleanupCommandTests(GitRepoTestCase):
    def test_derive_final_cleanup_commands_preserves_profiles(self) -> None:
        cleanup_commands = derive_final_cleanup_commands(
            [
                CommandSpec(
                    command="docker compose --profile test up test --build --abort-on-container-exit\n",
                    expected_outputs=[],
                ),
                CommandSpec(
                    command="docker compose run --rm mcp-test --enable-resiliency-tests\n",
                    expected_outputs=[],
                ),
            ]
        )

        self.assertEqual(
            cleanup_commands,
            [
                "docker compose --profile test down -v --remove-orphans",
                "docker compose down -v --remove-orphans",
            ],
        )

    def test_runs_only_cleanup_commands_before_next_expected_output_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cleanup_marker = temp_path / "cleanup.txt"
            later_marker = temp_path / "later.txt"

            results = run_cleanup_commands(
                [
                    CommandSpec(
                        command=f"kill -0 $$ >/dev/null 2>&1; printf done > {cleanup_marker.name}",
                        expected_outputs=[],
                    ),
                    CommandSpec(command=f"printf skip > {later_marker.name}", expected_outputs=[]),
                    CommandSpec(command="printf 'stop here\\n'", expected_outputs=["stop here\n"]),
                ],
                cwd=temp_path,
                timeout_seconds=5,
            )

            self.assertEqual(len(results), 1)
            self.assertTrue(cleanup_marker.exists())
            self.assertFalse(later_marker.exists())

    def test_reset_lab_changes_restores_new_tracked_changes_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            self._init_git_repo(repo_path)
            tracked_path = repo_path / "tracked.txt"
            preserved_path = repo_path / "preserved.txt"
            tracked_path.write_text("original\n", encoding="utf-8")
            preserved_path.write_text("keep me dirty\n", encoding="utf-8")
            self._git(repo_path, "add", "tracked.txt", "preserved.txt")
            self._git(repo_path, "commit", "-m", "init")
            preserved_path.write_text("user edit\n", encoding="utf-8")

            baseline = snapshot_repo_state(repo_path)
            tracked_path.write_text("lab edit\n", encoding="utf-8")
            created_path = repo_path / "created.txt"
            created_path.write_text("new file\n", encoding="utf-8")

            reset_summary = reset_lab_changes(repo_path, baseline)

            self.assertEqual(tracked_path.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(preserved_path.read_text(encoding="utf-8"), "user edit\n")
            self.assertFalse(created_path.exists())
            self.assertEqual(reset_summary.restored, [Path("tracked.txt")])
            self.assertEqual(reset_summary.removed, [Path("created.txt")])


class SkipCommandTests(GitRepoTestCase):
    def test_skip_rule_requires_both_docker_and_studio(self) -> None:
        self.assertTrue(should_skip_command("docker compose --profile studio up --build"))
        self.assertFalse(should_skip_command("docker compose up test --build"))
        self.assertFalse(should_skip_command("open specmatic studio"))


class MainTests(GitRepoTestCase):
    def test_resolve_readme_paths_uses_default_labs_when_no_arg(self) -> None:
        readme_paths = resolve_readme_paths(None)

        self.assertEqual(len(readme_paths), len(DEFAULT_LABS))
        self.assertTrue(str(readme_paths[0]).endswith("/api-coverage/README.md"))
        self.assertTrue(str(readme_paths[-1]).endswith("/workflow-in-same-spec/README.md"))

    def test_resolve_readme_paths_appends_readme_to_lab_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir) / "sample-lab"
            lab_path.mkdir()

            readme_paths = resolve_readme_paths(str(lab_path))

        self.assertEqual(readme_paths, [(lab_path / "README.md").resolve()])

    def test_main_returns_zero_for_valid_readme(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            readme_path = lab_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf 'ok\\n'
                    ```

                    ```terminaloutput
                    ok
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            exit_code = main([str(lab_path), "--timeout", "5"])

        self.assertEqual(exit_code, 0)

    def test_dry_run_prints_command_mapping(self) -> None:
        stdout_buffer = io.StringIO()
        command_specs = [
            CommandSpec(command="echo one\n", expected_outputs=["one\n", "two\n"]),
            CommandSpec(command="echo two\n", expected_outputs=[]),
        ]

        with redirect_stdout(stdout_buffer):
            print_command_mapping(command_specs)

        output = stdout_buffer.getvalue()
        self.assertIn("Command #1", output)
        self.assertIn("Shell", output)
        self.assertIn("expected terminaloutput blocks: 2", output)
        self.assertIn("  echo one", output)
        self.assertIn("  echo one\n\nterminaloutput #1", output)
        self.assertIn("terminaloutput #1", output)
        self.assertIn("  one", output)
        self.assertIn("terminaloutput #2", output)
        self.assertIn("  two", output)
        self.assertIn("Command #2", output)
        self.assertIn("terminaloutput  none", output)

    def test_cli_invocation_reports_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            readme_path = lab_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf 'actual\\n'
                    ```

                    ```terminaloutput
                    expected
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["python3", str(ROOT_DIR / "validate_readme_commands.py"), str(lab_path)],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("missing expected terminaloutput block #1", completed.stderr)
        self.assertTrue(completed.stdout.rstrip().endswith("FAIL"))

    def test_cli_invocation_prints_failure_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            readme_path = lab_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf 'actual\\n'
                    ```

                    ```terminaloutput
                    expected
                    ```

                    ```shell
                    printf 'later\\n'
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["python3", str(ROOT_DIR / "validate_readme_commands.py"), str(lab_path)],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("FAIL command #1", completed.stdout)
        self.assertIn("SKIP command #2", completed.stdout)
        self.assertTrue(completed.stdout.rstrip().endswith("FAIL"))

    def test_dry_run_does_not_execute_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            readme_path = lab_path / "README.md"
            marker_path = lab_path / "marker.txt"
            readme_path.write_text(
                textwrap.dedent(
                    f"""
                    ```shell
                    printf executed > {marker_path.name}
                    ```

                    ```terminaloutput
                    executed
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    str(ROOT_DIR / "validate_readme_commands.py"),
                    "--dry-run",
                    str(lab_path),
                ],
                cwd=str(lab_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertFalse(marker_path.exists())

        self.assertEqual(completed.returncode, 0)
        self.assertIn("Command #1", completed.stdout)

    def test_cli_invocation_prints_pass_at_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            self._init_git_repo(repo_path)
            readme_path = repo_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf ok
                    ```

                    ```terminaloutput
                    ok
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["python3", str(ROOT_DIR / "validate_readme_commands.py"), str(repo_path)],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("Command #1", completed.stdout)
        self.assertIn("expected terminaloutput blocks: 1", completed.stdout)
        self.assertTrue(completed.stdout.rstrip().endswith("PASS"))

    def test_main_resets_lab_changed_files_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            self._init_git_repo(repo_path)
            target_path = repo_path / "tracked.txt"
            target_path.write_text("original\n", encoding="utf-8")
            self._git(repo_path, "add", "tracked.txt")
            self._git(repo_path, "commit", "-m", "init")
            readme_path = repo_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf changed > tracked.txt
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["python3", str(ROOT_DIR / "validate_readme_commands.py"), str(repo_path)],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(target_path.read_text(encoding="utf-8"), "original\n")

        self.assertEqual(completed.returncode, 0)
        self.assertIn("RESET (restored: 1, removed: 0)", completed.stdout)

    def test_main_skip_reset_preserves_lab_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            self._init_git_repo(repo_path)
            target_path = repo_path / "tracked.txt"
            target_path.write_text("original\n", encoding="utf-8")
            self._git(repo_path, "add", "tracked.txt")
            self._git(repo_path, "commit", "-m", "init")
            readme_path = repo_path / "README.md"
            readme_path.write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf changed > tracked.txt
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    str(ROOT_DIR / "validate_readme_commands.py"),
                    "--skip-reset",
                    str(repo_path),
                ],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(target_path.read_text(encoding="utf-8"), "changed")

        self.assertEqual(completed.returncode, 0)
        self.assertNotIn("RESET", completed.stdout)

    def test_main_without_readme_runs_all_default_labs_and_continues_after_failure(self) -> None:
        fake_readmes = [
            Path("/tmp/lab-one/README.md"),
            Path("/tmp/lab-two/README.md"),
            Path("/tmp/lab-three/README.md"),
        ]
        stdout_buffer = io.StringIO()
        calls: list[Path] = []

        def fake_run_single_readme(*, readme_path: Path, dry_run: bool, skip_reset: bool, timeout_seconds: float) -> int:
            calls.append(readme_path)
            return 1 if readme_path == fake_readmes[1] else 0

        with (
            patch("validate_readme_commands.resolve_readme_paths", return_value=fake_readmes),
            patch("pathlib.Path.is_file", return_value=True),
            patch("validate_readme_commands.run_single_readme", side_effect=fake_run_single_readme),
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        self.assertEqual(calls, fake_readmes)
        output = stdout_buffer.getvalue()
        self.assertIn("===== lab-one =====", output)
        self.assertIn("===== lab-two =====", output)
        self.assertIn("===== lab-three =====", output)
        self.assertIn("===== Summary =====", output)
        self.assertIn("PASS labs: 2", output)
        self.assertIn("  lab-one", output)
        self.assertIn("  lab-three", output)
        self.assertIn("FAIL labs: 1", output)
        self.assertIn("  lab-two", output)

if __name__ == "__main__":
    unittest.main()
