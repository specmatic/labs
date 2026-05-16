import io
import json
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
    DockerWarmupResult,
    LabExecutionResult,
    PreflightCheckResult,
    PreflightRequirements,
    RunReport,
    _expected_output_matches,
    determine_preflight_requirements,
    derive_final_cleanup_commands,
    load_run_report,
    main,
    parse_readme_commands,
    print_command_mapping,
    print_run_report,
    run_preflight,
    warm_docker_images,
    write_run_report,
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

    def test_failure_message_shows_expected_and_closest_actual_line(self) -> None:
        with self.assertRaises(CommandExecutionError) as ctx:
            run_command_specs(
                [
                    CommandSpec(
                        command="printf 'Tests run: 1, Successes: 1, Failures: 0, WIP: 0, Errors: 0\\n'",
                        expected_outputs=["Tests run: 1, Successes: 1, Failures: 0, Errors: 0\n"],
                    )
                ],
                cwd=ROOT_DIR,
                timeout_seconds=5,
            )

        message = str(ctx.exception)
        self.assertIn("Mismatch Detail", message)
        self.assertIn("Expected line", message)
        self.assertIn("Tests run: 1, Successes: 1, Failures: 0, Errors: 0", message)
        self.assertIn("Closest actual line", message)
        self.assertIn("Tests run: 1, Successes: 1, Failures: 0, WIP: 0, Errors: 0", message)

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


class PreflightTests(GitRepoTestCase):
    def test_determine_preflight_requirements_for_non_docker_lab(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            (lab_path / "README.md").write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf 'ok\\n'
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            requirements = determine_preflight_requirements([lab_path / "README.md"])

        self.assertEqual(
            requirements,
            PreflightRequirements(
                docker_cli=False,
                docker_compose=False,
                license_validation=False,
                remote_contract_access=False,
            ),
        )

    def test_determine_preflight_requirements_for_repo_lab(self) -> None:
        requirements = determine_preflight_requirements([ROOT_DIR / "api-coverage" / "README.md"])

        self.assertEqual(
            requirements,
            PreflightRequirements(
                docker_cli=True,
                docker_compose=True,
                license_validation=True,
                remote_contract_access=False,
            ),
        )

    def test_run_preflight_returns_empty_when_no_checks_required(self) -> None:
        results = run_preflight(
            [Path("/tmp/sample/README.md")],
            PreflightRequirements(
                docker_cli=False,
                docker_compose=False,
                license_validation=False,
                remote_contract_access=False,
            ),
        )

        self.assertEqual(results, [])

    def test_run_preflight_reports_missing_docker(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            side_effect=OSError("No such file or directory: 'docker'"),
        ):
            results = run_preflight(
                [Path("/tmp/sample/README.md")],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=False,
                    license_validation=False,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[0].name, "docker")
        self.assertFalse(results[0].passed)
        self.assertIn("No such file or directory", results[0].detail or "")

    def test_run_preflight_reports_missing_docker_compose(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "compose", "version"],
                returncode=1,
                stdout="",
                stderr="docker: 'compose' is not a docker command",
            ),
        ):
            results = run_preflight(
                [Path("/tmp/sample/README.md")],
                PreflightRequirements(
                    docker_cli=False,
                    docker_compose=True,
                    license_validation=False,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[0].name, "docker compose")
        self.assertFalse(results[0].passed)
        self.assertIn("not a docker command", results[0].detail or "")

    def test_run_preflight_reports_unreachable_docker_daemon(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            side_effect=[
                subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "info"], returncode=1, stdout="", stderr="Cannot connect to the Docker daemon"),
            ],
        ):
            results = run_preflight(
                [Path("/tmp/sample/README.md")],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=False,
                    license_validation=False,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[1].name, "docker daemon")
        self.assertFalse(results[1].passed)
        self.assertIn("Cannot connect to the Docker daemon", results[1].detail or "")

    def test_run_preflight_reports_missing_license_file(self) -> None:
        with (
            patch(
                "validate_readme_commands.subprocess.run",
                side_effect=[
                    subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
                    subprocess.CompletedProcess(args=["docker", "compose", "version"], returncode=0, stdout="", stderr=""),
                    subprocess.CompletedProcess(args=["docker", "info"], returncode=0, stdout="", stderr=""),
                ],
            ),
            patch("validate_readme_commands.Path.is_file", return_value=False),
        ):
            results = run_preflight(
                [ROOT_DIR / "api-coverage" / "README.md"],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=True,
                    license_validation=True,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[3].name, "specmatic license file exists")
        self.assertFalse(results[3].passed)
        self.assertEqual(results[4].name, "specmatic license validation")
        self.assertFalse(results[4].passed)
        self.assertTrue(results[4].skipped)

    def test_run_preflight_reports_invalid_license(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            side_effect=[
                subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "compose", "version"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "info"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "run"], returncode=1, stdout="", stderr="License expired"),
            ],
        ) as mocked_run, patch("validate_readme_commands.Path.is_file", return_value=True):
            results = run_preflight(
                [ROOT_DIR / "api-coverage" / "README.md"],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=True,
                    license_validation=True,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[4].name, "specmatic license validation")
        self.assertFalse(results[4].passed)
        self.assertIn("License expired", results[4].detail or "")
        license_call = mocked_run.call_args_list[3]
        self.assertEqual(
            license_call.kwargs["cwd"],
            str(ROOT_DIR),
        )
        self.assertEqual(
            license_call.args[0],
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "./license.txt:/specmatic/specmatic-license.txt:ro",
                "-e",
                "SPECMATIC_LICENSE_PATH=/specmatic/specmatic-license.txt",
                "specmatic/enterprise:latest",
                "show-license",
            ],
        )

    def test_run_preflight_reports_expired_license_even_when_show_license_exits_zero(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            side_effect=[
                subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "compose", "version"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=["docker", "info"], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(
                    args=["docker", "run"],
                    returncode=0,
                    stdout=(
                        "WARNING: License loaded from /specmatic/specmatic-license.txt is expired as of May 16, 2026 at 6:30:32 AM UTC\n"
                        "Using Specmatic Trial license initialized from jar:file:/usr/local/share/enterprise/enterprise.jar!/specmatic-default-trial-license.txt\n"
                        "License details:\n"
                    ),
                    stderr="",
                ),
            ],
        ), patch("validate_readme_commands.Path.is_file", return_value=True):
            results = run_preflight(
                [ROOT_DIR / "api-coverage" / "README.md"],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=True,
                    license_validation=True,
                    remote_contract_access=False,
                ),
            )

        self.assertEqual(results[4].name, "specmatic license validation")
        self.assertFalse(results[4].passed)
        self.assertIn("is expired", results[4].detail or "")
        self.assertIn("initialized from jar:file:", results[4].detail or "")

    def test_run_preflight_skips_license_validation_when_not_required(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
        ) as mocked_run:
            results = run_preflight(
                [Path("/tmp/sample/README.md")],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=False,
                    license_validation=False,
                    remote_contract_access=False,
                ),
            )

        self.assertTrue(all(result.name != "specmatic license validation" for result in results))
        self.assertEqual(mocked_run.call_count, 2)

    def test_run_preflight_reports_remote_contract_access_failure(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["git", "ls-remote"], returncode=128, stdout="", stderr="Could not resolve host: github.com"),
        ):
            results = run_preflight(
                [ROOT_DIR / "response-templating" / "README.md"],
                PreflightRequirements(
                    docker_cli=False,
                    docker_compose=False,
                    license_validation=False,
                    remote_contract_access=True,
                ),
            )

        self.assertEqual(results[0].name, "labs-contracts access")
        self.assertFalse(results[0].passed)
        self.assertIn("Could not resolve host", results[0].detail or "")

    def test_run_preflight_skips_remote_contract_check_when_not_required(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["docker", "--version"], returncode=0, stdout="", stderr=""),
        ) as mocked_run:
            run_preflight(
                [Path("/tmp/sample/README.md")],
                PreflightRequirements(
                    docker_cli=True,
                    docker_compose=False,
                    license_validation=False,
                    remote_contract_access=False,
                ),
            )

        commands = [call.args[0] for call in mocked_run.call_args_list]
        self.assertNotIn(
            ["git", "ls-remote", "--exit-code", "https://github.com/specmatic/labs-contracts.git", "HEAD"],
            commands,
        )

    def test_warm_docker_images_skips_non_compose_lab(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lab_path = Path(temp_dir)
            (lab_path / "README.md").write_text(
                textwrap.dedent(
                    """
                    ```shell
                    printf 'ok\\n'
                    ```
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            results = warm_docker_images([lab_path / "README.md"])

        self.assertEqual(results, [])

    def test_warm_docker_images_runs_compose_pull_with_extended_timeout(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            return_value=subprocess.CompletedProcess(args=["docker", "compose", "pull"], returncode=0, stdout="", stderr=""),
        ) as mocked_run:
            results = warm_docker_images([ROOT_DIR / "api-coverage" / "README.md"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].lab_name, "api-coverage")
        self.assertTrue(results[0].passed)
        warmup_call = mocked_run.call_args_list[0]
        self.assertEqual(
            warmup_call.args[0],
            ["docker", "compose", "pull", "--ignore-buildable"],
        )
        self.assertEqual(warmup_call.kwargs["cwd"], str(ROOT_DIR / "api-coverage"))
        self.assertEqual(warmup_call.kwargs["timeout"], 300.0)

    def test_warm_docker_images_reports_timeout(self) -> None:
        with patch(
            "validate_readme_commands.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="docker compose pull", timeout=300),
        ):
            results = warm_docker_images([ROOT_DIR / "api-coverage" / "README.md"])

        self.assertEqual(results[0].lab_name, "api-coverage")
        self.assertFalse(results[0].passed)
        self.assertIn("timed out after 300 seconds", results[0].detail or "")


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

            with patch("validate_readme_commands.run_preflight", return_value=[]):
                with patch("validate_readme_commands.warm_docker_images", return_value=[]):
                    exit_code = main([str(lab_path), "--timeout", "5"])

        self.assertEqual(exit_code, 0)

    def test_main_single_lab_skips_preflight(self) -> None:
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

            with (
                patch("validate_readme_commands.run_preflight") as mocked_preflight,
                patch("validate_readme_commands.warm_docker_images", return_value=[]),
            ):
                exit_code = main([str(lab_path), "--timeout", "5"])

        self.assertEqual(exit_code, 0)
        mocked_preflight.assert_not_called()

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

        def fake_run_single_readme(
            *,
            readme_path: Path,
            dry_run: bool,
            skip_reset: bool,
            timeout_seconds: float,
        ) -> LabExecutionResult:
            calls.append(readme_path)
            if readme_path == fake_readmes[0]:
                return LabExecutionResult(
                    name="lab-one",
                    exit_code=0,
                    duration_seconds=0.0,
                    validated_commands=5,
                    total_commands=5,
                    skipped_commands=0,
                )
            if readme_path == fake_readmes[1]:
                return LabExecutionResult(
                    name="lab-two",
                    exit_code=1,
                    duration_seconds=0.0,
                    validated_commands=2,
                    total_commands=4,
                    skipped_commands=2,
                )
            return LabExecutionResult(
                name="lab-three",
                exit_code=0,
                duration_seconds=0.0,
                validated_commands=3,
                total_commands=5,
                skipped_commands=2,
            )

        with (
            patch("validate_readme_commands.resolve_readme_paths", return_value=fake_readmes),
            patch("pathlib.Path.is_file", return_value=True),
            patch("validate_readme_commands.run_preflight", return_value=[]),
            patch("validate_readme_commands.warm_docker_images", return_value=[]) as mocked_warmup,
            patch("validate_readme_commands.run_single_readme", side_effect=fake_run_single_readme),
            patch(
                "validate_readme_commands.time.perf_counter",
                side_effect=[0.0, 1.5, 1.5, 4.0, 4.0, 7.25],
            ),
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        warmed_readmes = [call.args[0][0] for call in mocked_warmup.call_args_list]
        self.assertEqual(warmed_readmes, fake_readmes)
        self.assertEqual(calls, fake_readmes)
        output = stdout_buffer.getvalue()
        self.assertIn("===== lab-one =====", output)
        self.assertIn("===== lab-two =====", output)
        self.assertIn("===== lab-three =====", output)
        self.assertIn("===== Summary =====", output)
        self.assertIn("PASS labs: 2", output)
        self.assertIn("FAIL labs: 1", output)
        self.assertIn("Lab", output)
        self.assertIn("Status", output)
        self.assertIn("Duration", output)
        self.assertIn("Validated", output)
        self.assertIn("Skipped", output)
        self.assertIn("lab-one    PASS", output)
        self.assertIn("1.50s", output)
        self.assertIn("5/5", output)
        self.assertIn("lab-three  PASS", output)
        self.assertIn("3.25s", output)
        self.assertIn("3/5", output)
        self.assertIn("lab-two    FAIL", output)
        self.assertIn("2.50s", output)
        self.assertIn("2/4", output)

    def test_main_aborts_before_running_labs_when_preflight_fails(self) -> None:
        stdout_buffer = io.StringIO()

        with (
            patch(
                "validate_readme_commands.resolve_readme_paths",
                return_value=[ROOT_DIR / "api-coverage" / "README.md"],
            ),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "validate_readme_commands.run_preflight",
                return_value=[
                    PreflightCheckResult(
                        name="docker daemon",
                        passed=False,
                        skipped=False,
                        detail="Docker is not running",
                        suggestion="Start Docker Desktop.",
                    )
                ],
            ),
            patch("validate_readme_commands.warm_docker_images") as mocked_warmup,
            patch("validate_readme_commands.run_single_readme") as mocked_run_single_readme,
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        mocked_warmup.assert_not_called()
        mocked_run_single_readme.assert_not_called()
        output = stdout_buffer.getvalue()
        self.assertIn("===== Preflight =====", output)
        self.assertIn("Preflight failed. No labs were executed.", output)
        self.assertNotIn("===== api-coverage =====", output)

    def test_print_preflight_results_uses_skip_for_dependent_checks(self) -> None:
        stdout_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer):
            from validate_readme_commands import print_preflight_results

            print_preflight_results(
                [
                    PreflightCheckResult(name="docker", passed=True),
                    PreflightCheckResult(
                        name="docker daemon",
                        passed=False,
                        detail="Docker is not running",
                        suggestion="Start Docker Desktop.",
                    ),
                    PreflightCheckResult(
                        name="specmatic license validation",
                        passed=False,
                        skipped=True,
                        detail="skipped because Docker or the license file is unavailable",
                        suggestion="Fix Docker access and the license file, then rerun the validator.",
                    ),
                ]
            )

        output = stdout_buffer.getvalue()
        self.assertIn("PASS docker", output)
        self.assertIn("FAIL docker daemon: Docker is not running", output)
        self.assertIn("SKIP specmatic license validation: skipped because Docker or the license file is unavailable", output)

    def test_main_prints_preflight_once_then_runs_labs(self) -> None:
        stdout_buffer = io.StringIO()
        fake_readmes = [Path("/tmp/lab-one/README.md")]

        with (
            patch("validate_readme_commands.resolve_readme_paths", return_value=fake_readmes),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "validate_readme_commands.run_preflight",
                return_value=[PreflightCheckResult(name="docker", passed=True)],
            ),
            patch("validate_readme_commands.warm_docker_images", return_value=[]),
            patch(
                "validate_readme_commands.run_single_readme",
                return_value=LabExecutionResult(
                    name="lab-one",
                    exit_code=0,
                    duration_seconds=0.0,
                    validated_commands=1,
                    total_commands=1,
                    skipped_commands=0,
                ),
            ),
            patch("validate_readme_commands.time.perf_counter", side_effect=[0.0, 1.0]),
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        output = stdout_buffer.getvalue()
        self.assertEqual(output.count("===== Preflight ====="), 1)
        self.assertIn("PASS docker", output)

    def test_main_marks_current_lab_failed_when_docker_warmup_fails(self) -> None:
        stdout_buffer = io.StringIO()
        fake_readmes = [Path("/tmp/lab-one/README.md"), Path("/tmp/lab-two/README.md")]

        with (
            patch("validate_readme_commands.resolve_readme_paths", return_value=fake_readmes),
            patch("pathlib.Path.is_file", return_value=True),
            patch("validate_readme_commands.run_preflight", return_value=[]),
            patch(
                "validate_readme_commands.warm_docker_images",
                side_effect=[
                    [DockerWarmupResult(lab_name="lab-one", passed=False, detail="timed out after 300 seconds")],
                    [],
                ],
            ),
            patch(
                "validate_readme_commands.run_single_readme",
                return_value=LabExecutionResult(
                    name="lab-two",
                    exit_code=0,
                    duration_seconds=0.0,
                    validated_commands=1,
                    total_commands=1,
                    skipped_commands=0,
                ),
            ) as mocked_run_single_readme,
            patch("validate_readme_commands.time.perf_counter", side_effect=[0.0, 1.0, 1.0, 2.0]),
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        mocked_run_single_readme.assert_called_once_with(
            readme_path=fake_readmes[1],
            dry_run=False,
            skip_reset=False,
            timeout_seconds=120.0,
        )
        output = stdout_buffer.getvalue()
        self.assertIn("===== lab-one =====", output)
        self.assertIn("===== Docker Warmup =====", output)
        self.assertIn("FAIL lab-one: timed out after 300 seconds", output)
        self.assertIn("===== lab-two =====", output)
        self.assertIn("PASS labs: 1", output)
        self.assertIn("FAIL labs: 1", output)

    def test_main_dry_run_summary_does_not_report_pass_or_fail(self) -> None:
        fake_readmes = [
            Path("/tmp/lab-one/README.md"),
            Path("/tmp/lab-two/README.md"),
        ]
        stdout_buffer = io.StringIO()

        def fake_run_single_readme(
            *,
            readme_path: Path,
            dry_run: bool,
            skip_reset: bool,
            timeout_seconds: float,
        ) -> LabExecutionResult:
            self.assertTrue(dry_run)
            if readme_path == fake_readmes[0]:
                return LabExecutionResult(
                    name="lab-one",
                    exit_code=0,
                    duration_seconds=0.0,
                    validated_commands=0,
                    total_commands=5,
                    skipped_commands=0,
                )
            return LabExecutionResult(
                name="lab-two",
                exit_code=0,
                duration_seconds=0.0,
                validated_commands=0,
                total_commands=3,
                skipped_commands=0,
            )

        with (
            patch("validate_readme_commands.resolve_readme_paths", return_value=fake_readmes),
            patch("pathlib.Path.is_file", return_value=True),
            patch("validate_readme_commands.run_single_readme", side_effect=fake_run_single_readme),
            patch("validate_readme_commands.time.perf_counter", side_effect=[0.0, 1.0, 1.0, 2.0]),
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main(["--dry-run"])

        self.assertEqual(exit_code, 0)
        output = stdout_buffer.getvalue()
        self.assertIn("===== Summary =====", output)
        self.assertIn("DRY RUN labs: 2", output)
        self.assertIn("Lab", output)
        self.assertIn("Status", output)
        self.assertIn("Duration", output)
        self.assertIn("Commands", output)
        self.assertIn("lab-one  DRY RUN", output)
        self.assertIn("lab-two  DRY RUN", output)
        self.assertIn("1.00s", output)
        self.assertIn("5", output)
        self.assertIn("3", output)
        self.assertNotIn("PASS labs:", output)
        self.assertNotIn("FAIL labs:", output)

    def test_main_preflight_only_runs_checks_and_exits(self) -> None:
        stdout_buffer = io.StringIO()

        with (
            patch(
                "validate_readme_commands.run_preflight",
                return_value=[PreflightCheckResult(name="docker", passed=True)],
            ),
            patch("validate_readme_commands.run_single_readme") as mocked_run_single_readme,
            redirect_stdout(stdout_buffer),
        ):
            exit_code = main(["--preflight-only"])

        self.assertEqual(exit_code, 0)
        mocked_run_single_readme.assert_not_called()
        output = stdout_buffer.getvalue()
        self.assertIn("===== Preflight =====", output)

    def test_main_writes_result_json_for_single_lab(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"

            with (
                patch(
                    "validate_readme_commands.resolve_readme_paths",
                    return_value=[Path("/tmp/lab-one/README.md")],
                ),
                patch("pathlib.Path.is_file", return_value=True),
                patch("validate_readme_commands.warm_docker_images", return_value=[]),
                patch(
                    "validate_readme_commands.run_single_readme",
                    return_value=LabExecutionResult(
                        name="lab-one",
                        exit_code=0,
                        duration_seconds=0.0,
                        validated_commands=2,
                        total_commands=2,
                        skipped_commands=0,
                    ),
                ),
                patch("validate_readme_commands.time.perf_counter", side_effect=[0.0, 1.0]),
            ):
                exit_code = main(["/tmp/lab-one", "--result-json", str(result_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "execution")
            self.assertEqual(payload["labs"][0]["name"], "lab-one")

    def test_load_and_print_run_report_from_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = Path(temp_dir)
            write_run_report(
                result_dir / "lab-one.json",
                RunReport(
                    mode="execution",
                    labs=[
                        LabExecutionResult(
                            name="lab-one",
                            exit_code=0,
                            duration_seconds=1.5,
                            validated_commands=5,
                            total_commands=5,
                            skipped_commands=0,
                        )
                    ],
                ),
            )
            write_run_report(
                result_dir / "lab-two.json",
                RunReport(
                    mode="execution",
                    labs=[
                        LabExecutionResult(
                            name="lab-two",
                            exit_code=1,
                            duration_seconds=2.5,
                            validated_commands=2,
                            total_commands=4,
                            skipped_commands=2,
                        )
                    ],
                ),
            )

            report = load_run_report(result_dir)
            stdout_buffer = io.StringIO()
            with redirect_stdout(stdout_buffer):
                print_run_report(report)

        output = stdout_buffer.getvalue()
        self.assertIn("PASS labs: 1", output)
        self.assertIn("FAIL labs: 1", output)
        self.assertIn("lab-one", output)
        self.assertIn("lab-two", output)

    def test_main_report_from_directory_prints_consolidated_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = Path(temp_dir)
            (result_dir / "lab-one.json").write_text(
                json.dumps(
                    {
                        "mode": "execution",
                        "labs": [
                            {
                                "name": "lab-one",
                                "exit_code": 0,
                                "duration_seconds": 1.0,
                                "validated_commands": 1,
                                "total_commands": 1,
                                "skipped_commands": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout_buffer = io.StringIO()
            with redirect_stdout(stdout_buffer):
                exit_code = main(["--report-from", str(result_dir)])

        self.assertEqual(exit_code, 0)
        self.assertIn("===== Summary =====", stdout_buffer.getvalue())

if __name__ == "__main__":
    unittest.main()
