#!/usr/bin/env python3
"""Validate shell commands and expected terminal output in a README."""

from __future__ import annotations

import argparse
import difflib
import json
import queue
import shutil
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_DIM = "\033[2m"
DOCKER_WARMUP_TIMEOUT_SECONDS = 300.0

DEFAULT_LABS = [
    "api-coverage",
    "schema-design",
    "response-templating",
    "api-resiliency-testing",
    "api-security-schemes",
    "async-event-flow",
    "backward-compatibility-testing",
    "continuous-integration",
    "data-adapters",
    "dictionary",
    "external-examples",
    "filters",
    "kafka-avro",
    "kafka-sqs-retry-dlq",
    "mcp-auto-test",
    "overlays",
    "partial-examples",
    "quick-start-api-testing",
    "quick-start-async-contract-testing",
    "quick-start-contract-testing",
    "quick-start-mock",
    "schema-resiliency-testing",
    "workflow-in-same-spec",
]


@dataclass(frozen=True)
class ValidationRunSummary:
    results: list["CommandResult"]
    failure_message: str | None = None
    failed_index: int | None = None


@dataclass(frozen=True)
class CommandSpec:
    command: str
    expected_outputs: list[str]


@dataclass(frozen=True)
class CommandResult:
    index: int
    command: str
    expected_outputs: list[str]
    cwd: Path
    skipped: bool
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined_output(self) -> str:
        return f"{self.stdout}{self.stderr}"


@dataclass(frozen=True)
class FencedBlock:
    language: str
    content: str


@dataclass(frozen=True)
class RepoSnapshot:
    repo_root: Path
    scope: Path
    tracked_dirty: set[Path]
    untracked: set[Path]


@dataclass(frozen=True)
class ResetSummary:
    restored: list[Path]
    removed: list[Path]


@dataclass(frozen=True)
class LabExecutionResult:
    name: str
    exit_code: int
    duration_seconds: float
    validated_commands: int
    total_commands: int
    skipped_commands: int


@dataclass(frozen=True)
class PreflightRequirements:
    docker_cli: bool
    docker_compose: bool
    license_validation: bool
    remote_contract_access: bool

    @property
    def any_required(self) -> bool:
        return any(
            (
                self.docker_cli,
                self.docker_compose,
                self.license_validation,
                self.remote_contract_access,
            )
        )


@dataclass(frozen=True)
class PreflightCheckResult:
    name: str
    passed: bool
    skipped: bool = False
    detail: str | None = None
    suggestion: str | None = None


@dataclass(frozen=True)
class DockerWarmupResult:
    lab_name: str
    passed: bool
    detail: str | None = None


@dataclass(frozen=True)
class RunReport:
    mode: str
    labs: list[LabExecutionResult]


class ReadmeValidationError(Exception):
    """Base error for README command validation."""


class ReadmeParseError(ReadmeValidationError):
    """Raised when the README structure is invalid."""


class CommandExecutionError(ReadmeValidationError):
    """Raised when a command times out or output validation fails."""


class CommandValidationFailure(CommandExecutionError):
    """Raised when a command output does not satisfy expectations."""


class ValidationStopped(CommandExecutionError):
    """Raised when validation stops early and a summary should still be printed."""

    def __init__(self, summary: ValidationRunSummary) -> None:
        super().__init__(summary.failure_message or "Validation stopped.")
        self.summary = summary


class GitInteractionError(ReadmeValidationError):
    """Raised when git state cannot be inspected or restored."""


def _supports_color() -> bool:
    return sys.stdout.isatty()


def _style(text: str, *codes: str) -> str:
    if not _supports_color() or not codes:
        return text
    return f"{''.join(codes)}{text}{ANSI_RESET}"


def should_skip_command(command: str) -> bool:
    normalized_command = command.lower()
    return "docker" in normalized_command and "studio" in normalized_command


def parse_readme_commands(readme_path: Path) -> list[CommandSpec]:
    lines = readme_path.read_text(encoding="utf-8").splitlines(keepends=True)
    blocks = _parse_fenced_blocks(lines)

    commands: list[CommandSpec] = []
    for block_index, block in enumerate(blocks):
        if block.language != "shell":
            continue

        expected_outputs: list[str] = []
        next_shell_index = len(blocks)
        for later_index in range(block_index + 1, len(blocks)):
            if blocks[later_index].language == "shell":
                next_shell_index = later_index
                break

        for later_block in blocks[block_index + 1 : next_shell_index]:
            if later_block.language == "terminaloutput":
                expected_outputs.append(later_block.content)

        commands.append(
            CommandSpec(
                command=block.content,
                expected_outputs=expected_outputs,
            )
        )

    return commands


def _parse_fenced_blocks(lines: Sequence[str]) -> list[FencedBlock]:
    blocks: list[FencedBlock] = []
    current_language: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if current_language is None:
            if stripped.startswith("```"):
                current_language = stripped[3:].strip()
                current_lines = []
            continue

        if stripped == "```":
            blocks.append(FencedBlock(language=current_language, content="".join(current_lines)))
            current_language = None
            current_lines = []
            continue

        current_lines.append(line)

    if current_language is not None:
        raise ReadmeParseError("Unterminated fenced code block in README.")

    return blocks


def run_command_specs(
    command_specs: Sequence[CommandSpec],
    cwd: Path,
    timeout_seconds: float,
) -> ValidationRunSummary:
    results: list[CommandResult] = []

    for index, command_spec in enumerate(command_specs, start=1):
        if should_skip_command(command_spec.command):
            results.append(_build_result(index=index, command_spec=command_spec, cwd=cwd, skipped=True))
            continue

        try:
            completed = _run_command(
                command=command_spec.command,
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            results.append(
                _build_result(
                    index=index,
                    command_spec=command_spec,
                    cwd=cwd,
                    returncode=-1,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                )
            )
            raise ValidationStopped(
                ValidationRunSummary(
                    results=results,
                    failure_message=_format_failure_message(
                        index=index,
                        command=command_spec.command,
                        expected_outputs=command_spec.expected_outputs,
                        cwd=cwd,
                        returncode=None,
                        reason=f"timed out after {timeout_seconds} seconds",
                    ),
                    failed_index=index,
                )
            ) from exc

        result = _build_result(
            index=index,
            command_spec=command_spec,
            cwd=cwd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

        try:
            _assert_command_result(result)
        except CommandValidationFailure as exc:
            results.append(result)
            print(
                f"Validation failed at command #{index}. "
                "Skipping remaining commands and running cleanup commands...",
                file=sys.stderr,
                flush=True,
            )
            cleanup_results = run_cleanup_commands(
                command_specs=command_specs[index:],
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
            if cleanup_results:
                raise ValidationStopped(
                    ValidationRunSummary(
                        results=results,
                        failure_message=(
                            f"{exc}\nCleanup commands executed:\n"
                            f"{_format_cleanup_results(cleanup_results)}"
                        ),
                        failed_index=index,
                    )
                ) from exc
            raise ValidationStopped(
                ValidationRunSummary(
                    results=results,
                    failure_message=str(exc),
                    failed_index=index,
                )
            ) from exc

        results.append(result)

    return ValidationRunSummary(results=results)


def _assert_command_result(result: CommandResult) -> None:
    if result.expected_outputs:
        for output_index, expected_output in enumerate(result.expected_outputs, start=1):
            if not _expected_output_matches(expected_output, result.combined_output):
                mismatch_detail = _describe_output_mismatch(expected_output, result.combined_output)
                raise CommandValidationFailure(
                    _format_failure_message(
                        index=result.index,
                        command=result.command,
                        expected_outputs=result.expected_outputs,
                        cwd=result.cwd,
                        returncode=result.returncode,
                        reason=f"missing expected terminaloutput block #{output_index}",
                        detail=mismatch_detail,
                    )
                )
        return

    if result.returncode != 0:
        raise CommandValidationFailure(
            _format_failure_message(
                index=result.index,
                command=result.command,
                expected_outputs=result.expected_outputs,
                cwd=result.cwd,
                returncode=result.returncode,
                reason="command exited non-zero without any expected terminaloutput blocks",
            )
        )


def _expected_output_matches(expected_output: str, actual_output: str) -> bool:
    expected_lines = [line for line in expected_output.splitlines() if line.strip()]
    actual_lines = actual_output.splitlines()

    if not expected_lines:
        return True

    actual_index = 0
    for expected_line in expected_lines:
        while actual_index < len(actual_lines):
            if expected_line in actual_lines[actual_index]:
                actual_index += 1
                break
            actual_index += 1
        else:
            return False

    return True


def _describe_output_mismatch(expected_output: str, actual_output: str) -> str | None:
    expected_lines = [line for line in expected_output.splitlines() if line.strip()]
    actual_lines = actual_output.splitlines()

    if not expected_lines:
        return None

    actual_index = 0
    for expected_line in expected_lines:
        while actual_index < len(actual_lines):
            if expected_line in actual_lines[actual_index]:
                actual_index += 1
                break
            actual_index += 1
        else:
            closest_line = _find_closest_line(expected_line, actual_lines)
            divider = _style("-" * 48, ANSI_DIM)
            detail_lines = [
                "",
                divider,
                _style("Mismatch Detail", ANSI_BOLD, ANSI_RED),
                "",
                _style("Expected line", ANSI_BOLD, ANSI_GREEN),
                f"  {expected_line}",
            ]
            if closest_line is not None:
                detail_lines.extend(
                    [
                        "",
                        _style("Closest actual line", ANSI_BOLD, ANSI_YELLOW),
                        f"  {closest_line}",
                    ]
                )
            else:
                detail_lines.extend(
                    [
                        "",
                        _style("Closest actual line", ANSI_BOLD, ANSI_YELLOW),
                        "  none",
                    ]
                )
            detail_lines.extend(["", divider])
            return "\n".join(detail_lines)

    return None


def _find_closest_line(expected_line: str, actual_lines: Sequence[str]) -> str | None:
    best_line: str | None = None
    best_ratio = 0.0

    for actual_line in actual_lines:
        ratio = difflib.SequenceMatcher(None, expected_line, actual_line).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_line = actual_line

    if best_ratio == 0.0:
        return None

    return best_line


def _run_command(
    *,
    command: str,
    cwd: Path,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    assert process.stderr is not None

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    output_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()

    def _reader(stream_name: str, stream, chunks: list[str]) -> None:
        try:
            for line in iter(stream.readline, ""):
                chunks.append(line)
                output_queue.put((stream_name, line))
        finally:
            stream.close()
            output_queue.put((stream_name, None))

    stdout_thread = threading.Thread(
        target=_reader,
        args=("stdout", process.stdout, stdout_chunks),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_reader,
        args=("stderr", process.stderr, stderr_chunks),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    finished_streams = 0
    timed_out = False
    deadline = time.monotonic() + timeout_seconds

    try:
        while finished_streams < 2:
            if process.poll() is None and time.monotonic() > deadline:
                timed_out = True
                process.kill()
                process.wait()
                raise subprocess.TimeoutExpired(
                    cmd=command,
                    timeout=timeout_seconds,
                    output="".join(stdout_chunks),
                    stderr="".join(stderr_chunks),
                )

            try:
                stream_name, chunk = output_queue.get(timeout=0.1)
            except queue.Empty:
                if process.poll() is not None:
                    continue
                continue

            if chunk is None:
                finished_streams += 1
                continue

            target_stream = sys.stdout if stream_name == "stdout" else sys.stderr
            print(chunk, end="", file=target_stream, flush=True)
    except Exception:
        process.kill()
        process.wait()
        raise

    try:
        returncode = process.wait(timeout=0)
    finally:
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        if not timed_out and process.poll() is None:
            process.kill()
            process.wait()

    return subprocess.CompletedProcess(
        args=command,
        returncode=returncode,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
    )


def run_cleanup_commands(
    command_specs: Sequence[CommandSpec],
    cwd: Path,
    timeout_seconds: float,
) -> list[CommandResult]:
    cleanup_results: list[CommandResult] = []

    for cleanup_index, command_spec in enumerate(command_specs, start=1):
        if command_spec.expected_outputs:
            break
        if not _is_cleanup_command(command_spec.command):
            continue

        try:
            completed = _run_command(
                command=command_spec.command,
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            continue
        cleanup_results.append(
            _build_result(
                index=cleanup_index,
                command_spec=command_spec,
                cwd=cwd,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )

    return cleanup_results


def run_final_cleanup_commands(
    command_specs: Sequence[CommandSpec],
    cwd: Path,
    timeout_seconds: float,
) -> list[CommandResult]:
    cleanup_results: list[CommandResult] = []

    for cleanup_index, cleanup_command in enumerate(derive_final_cleanup_commands(command_specs), start=1):
        try:
            completed = _run_command(
                command=cleanup_command,
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            continue
        cleanup_results.append(
            CommandResult(
                index=cleanup_index,
                command=cleanup_command,
                expected_outputs=[],
                cwd=cwd,
                skipped=False,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )

    return cleanup_results


def derive_final_cleanup_commands(command_specs: Sequence[CommandSpec]) -> list[str]:
    cleanup_commands: list[str] = []
    seen: set[str] = set()

    for command_spec in command_specs:
        cleanup_command = _derive_cleanup_command(command_spec.command)
        if cleanup_command is None or cleanup_command in seen:
            continue
        seen.add(cleanup_command)
        cleanup_commands.append(cleanup_command)

    return cleanup_commands


def _derive_cleanup_command(command: str) -> str | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    if len(tokens) >= 2 and tokens[0] == "docker" and tokens[1] == "compose":
        compose_start_index = 2
    elif tokens and tokens[0] == "docker-compose":
        compose_start_index = 1
    else:
        return None

    subcommand_index = None
    for index in range(compose_start_index, len(tokens)):
        if tokens[index] in {"up", "run"}:
            subcommand_index = index
            break

    if subcommand_index is None:
        return None

    cleanup_tokens = tokens[:subcommand_index] + ["down", "-v", "--remove-orphans"]
    return shlex.join(cleanup_tokens)


def _is_cleanup_command(command: str) -> bool:
    normalized_command = " ".join(command.lower().split())
    cleanup_patterns = (
        "docker compose down",
        "docker-compose down",
        "docker stop",
        "docker rm",
        "docker container rm",
        "kubectl delete",
        "pkill ",
        "kill ",
    )
    return any(pattern in normalized_command for pattern in cleanup_patterns)


def _format_cleanup_results(cleanup_results: Sequence[CommandResult]) -> str:
    lines: list[str] = []
    for result in cleanup_results:
        lines.append(f"- `{result.command.strip()}` exited with {result.returncode}")
    return "\n".join(lines)


def print_final_cleanup_summary(cleanup_results: Sequence[CommandResult]) -> None:
    if not cleanup_results:
        return

    print("FINAL CLEANUP")
    for result in cleanup_results:
        print(f"  {result.command}")


def _format_failure_message(
    *,
    index: int,
    command: str,
    expected_outputs: Sequence[str],
    cwd: Path | None,
    returncode: int | None,
    reason: str,
    detail: str | None = None,
) -> str:
    returncode_text = "n/a" if returncode is None else str(returncode)
    lines = [
        f"Command #{index} failed: {reason}",
        f"Exit code: {returncode_text}",
    ]
    if cwd is not None:
        lines.append(f"Working directory: {cwd}")
    lines.extend(
        [
            "Command:",
            command.rstrip("\n"),
            f"Expected terminaloutput blocks: {len(expected_outputs)}",
        ]
    )
    if detail:
        lines.extend(["", detail])
    return "\n".join(lines)


def _build_result(
    *,
    index: int,
    command_spec: CommandSpec,
    cwd: Path,
    skipped: bool = False,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> CommandResult:
    return CommandResult(
        index=index,
        command=command_spec.command,
        expected_outputs=command_spec.expected_outputs,
        cwd=cwd,
        skipped=skipped,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate README shell commands against terminaloutput blocks."
    )
    parser.add_argument(
        "readme",
        nargs="?",
        help="Lab directory to validate. If omitted, runs the built-in lab README list.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the README and print command-to-terminaloutput mappings without running commands.",
    )
    parser.add_argument(
        "--skip-reset",
        action="store_true",
        help="Do not reset lab-changed files back to their original git state at the end of the run.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Timeout in seconds for each shell command. Default: 120.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run only the shared preflight checks and exit.",
    )
    parser.add_argument(
        "--result-json",
        help="Write a machine-readable JSON result for this invocation.",
    )
    parser.add_argument(
        "--report-from",
        help="Read per-run JSON results from a directory and print a consolidated report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.preflight_only and (args.readme or args.dry_run or args.report_from):
        parser.error("--preflight-only cannot be combined with a lab path, --dry-run, or --report-from")
    if args.report_from and (args.readme or args.dry_run or args.preflight_only):
        parser.error("--report-from cannot be combined with a lab path, --dry-run, or --preflight-only")

    if args.report_from:
        report = load_run_report(Path(args.report_from))
        print_run_report(report)
        exit_code = 1 if any(lab.exit_code != 0 for lab in report.labs) else 0
        if args.result_json:
            write_run_report(Path(args.result_json), report)
        return exit_code

    readme_paths = resolve_readme_paths(args.readme)
    multiple_labs = len(readme_paths) > 1
    for readme_path in readme_paths:
        if not readme_path.is_file():
            parser.error(f"README file does not exist: {readme_path}")

    should_run_preflight = not args.dry_run and (args.preflight_only or args.readme is None)
    if should_run_preflight:
        requirements = determine_preflight_requirements(readme_paths)
        streamed_preflight = requirements.any_required
        if streamed_preflight:
            print("===== Preflight =====")
        preflight_results = run_preflight(
            readme_paths,
            requirements,
            on_result=_print_preflight_result,
        )
        if preflight_results:
            if not streamed_preflight:
                print_preflight_results(preflight_results)
            if any(not result.passed and not result.skipped for result in preflight_results):
                print("Preflight failed. No labs were executed.")
                if args.result_json:
                    write_run_report(Path(args.result_json), RunReport(mode="preflight-only", labs=[]))
                return 1
        if args.preflight_only:
            if args.result_json:
                write_run_report(Path(args.result_json), RunReport(mode="preflight-only", labs=[]))
            return 0

    overall_exit_code = 0
    passed_labs: list[LabExecutionResult] = []
    failed_labs: list[LabExecutionResult] = []
    for index, readme_path in enumerate(readme_paths, start=1):
        if multiple_labs:
            if index > 1:
                print()
            print(f"===== {readme_path.parent.name} =====")
        start_time = time.perf_counter()
        if not args.dry_run:
            streamed_warmup = bool(_docker_compose_lab_dirs([readme_path]))
            docker_warmup_results = warm_docker_images(
                [readme_path],
                on_result=_print_docker_warmup_result,
            )
            if docker_warmup_results:
                if not streamed_warmup:
                    print_docker_warmup_results(docker_warmup_results)
                if any(not result.passed for result in docker_warmup_results):
                    print("FAIL")
                    overall_exit_code = 1
                    failed_labs.append(
                        LabExecutionResult(
                            name=readme_path.parent.name,
                            exit_code=1,
                            duration_seconds=time.perf_counter() - start_time,
                            validated_commands=0,
                            total_commands=0,
                            skipped_commands=0,
                        )
                    )
                    continue
        lab_result = run_single_readme(
            readme_path=readme_path,
            dry_run=args.dry_run,
            skip_reset=args.skip_reset,
            timeout_seconds=args.timeout,
        )
        lab_result = LabExecutionResult(
            name=lab_result.name,
            exit_code=lab_result.exit_code,
            duration_seconds=time.perf_counter() - start_time,
            validated_commands=lab_result.validated_commands,
            total_commands=lab_result.total_commands,
            skipped_commands=lab_result.skipped_commands,
        )
        if lab_result.exit_code != 0:
            overall_exit_code = lab_result.exit_code
            failed_labs.append(lab_result)
        else:
            passed_labs.append(lab_result)

    if multiple_labs:
        print()
        print_multi_lab_summary(passed_labs, failed_labs, dry_run=args.dry_run)

    report_mode = "dry-run" if args.dry_run else "execution"
    if args.result_json:
        write_run_report(Path(args.result_json), RunReport(mode=report_mode, labs=[*passed_labs, *failed_labs]))

    return overall_exit_code


def run_single_readme(
    *,
    readme_path: Path,
    dry_run: bool,
    skip_reset: bool,
    timeout_seconds: float,
) -> LabExecutionResult:
    repo_snapshot = None if skip_reset else snapshot_repo_state(readme_path.parent)
    lab_name = readme_path.parent.name
    try:
        command_specs = parse_readme_commands(readme_path)
        if dry_run:
            print_command_mapping(command_specs)
            return LabExecutionResult(
                name=lab_name,
                exit_code=0,
                duration_seconds=0.0,
                validated_commands=0,
                total_commands=len(command_specs),
                skipped_commands=0,
            )
        print_command_mapping(command_specs)
        summary = run_command_specs(
            command_specs=command_specs,
            cwd=readme_path.parent,
            timeout_seconds=timeout_seconds,
        )
        exit_code = 0
    except ValidationStopped as exc:
        summary = exc.summary
        exit_code = 1
    except ReadmeValidationError as exc:
        print(f"README: {readme_path}", file=sys.stderr)
        print(exc, file=sys.stderr)
        return LabExecutionResult(
            name=lab_name,
            exit_code=1,
            duration_seconds=0.0,
            validated_commands=0,
            total_commands=0,
            skipped_commands=0,
        )

    print_run_summary(summary, total_commands=len(command_specs))

    if summary.failure_message is not None:
        print(f"README: {readme_path}", file=sys.stderr)
        print(summary.failure_message, file=sys.stderr)

    final_cleanup_results = run_final_cleanup_commands(
        command_specs=command_specs,
        cwd=readme_path.parent,
        timeout_seconds=timeout_seconds,
    )
    if final_cleanup_results:
        print_final_cleanup_summary(final_cleanup_results)

    if repo_snapshot is not None:
        print_reset_summary(reset_lab_changes(readme_path.parent, repo_snapshot))

    if exit_code == 0:
        print(f"Validated {len(summary.results)} command(s) in {readme_path}")
        print("PASS")
    else:
        print("FAIL")
    skipped_commands = sum(1 for result in summary.results if result.skipped)
    validated_commands = len(summary.results) - skipped_commands
    return LabExecutionResult(
        name=lab_name,
        exit_code=exit_code,
        duration_seconds=0.0,
        validated_commands=validated_commands,
        total_commands=len(command_specs),
        skipped_commands=total_commands_skipped(summary, len(command_specs)),
    )


def resolve_readme_paths(readme_arg: str | None) -> list[Path]:
    if readme_arg:
        return [(Path(readme_arg).expanduser().resolve() / "README.md")]

    repo_root = Path(__file__).resolve().parent
    return [(repo_root / lab / "README.md").resolve() for lab in DEFAULT_LABS]


def write_run_report(path: Path, report: RunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "mode": report.mode,
                "labs": [
                    {
                        "name": lab.name,
                        "exit_code": lab.exit_code,
                        "duration_seconds": lab.duration_seconds,
                        "validated_commands": lab.validated_commands,
                        "total_commands": lab.total_commands,
                        "skipped_commands": lab.skipped_commands,
                    }
                    for lab in report.labs
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_run_report(path: Path) -> RunReport:
    report_files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    labs: list[LabExecutionResult] = []
    modes: set[str] = set()

    for report_file in report_files:
        payload = json.loads(report_file.read_text(encoding="utf-8"))
        modes.add(payload.get("mode", "execution"))
        for lab in payload.get("labs", []):
            labs.append(
                LabExecutionResult(
                    name=lab["name"],
                    exit_code=lab["exit_code"],
                    duration_seconds=lab["duration_seconds"],
                    validated_commands=lab["validated_commands"],
                    total_commands=lab["total_commands"],
                    skipped_commands=lab["skipped_commands"],
                )
            )

    merged_mode = "dry-run" if modes == {"dry-run"} else "execution"
    return RunReport(mode=merged_mode, labs=sorted(labs, key=lambda lab: lab.name))


def print_run_report(report: RunReport) -> None:
    passed_labs = [lab for lab in report.labs if lab.exit_code == 0]
    failed_labs = [lab for lab in report.labs if lab.exit_code != 0]
    print_multi_lab_summary(
        passed_labs,
        failed_labs,
        dry_run=report.mode == "dry-run",
    )


def determine_preflight_requirements(readme_paths: Sequence[Path]) -> PreflightRequirements:
    docker_cli = False
    docker_compose = False
    license_validation = False
    remote_contract_access = False

    for readme_path in readme_paths:
        if _readme_uses_docker(readme_path):
            docker_cli = True
        if _readme_uses_docker_compose(readme_path):
            docker_compose = True

        for config_path in _related_config_paths(readme_path.parent):
            if not config_path.is_file():
                continue
            try:
                config_text = config_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "/specmatic/specmatic-license.txt" in config_text:
                license_validation = True
            if "https://github.com/specmatic/labs-contracts.git" in config_text:
                remote_contract_access = True

    return PreflightRequirements(
        docker_cli=docker_cli,
        docker_compose=docker_compose,
        license_validation=license_validation,
        remote_contract_access=remote_contract_access,
    )


def _readme_uses_docker(readme_path: Path) -> bool:
    try:
        command_specs = parse_readme_commands(readme_path)
    except (OSError, ReadmeValidationError):
        return False
    return any("docker" in command_spec.command.lower() for command_spec in command_specs)


def _readme_uses_docker_compose(readme_path: Path) -> bool:
    try:
        command_specs = parse_readme_commands(readme_path)
    except (OSError, ReadmeValidationError):
        return False
    return any(
        "docker compose" in command_spec.command.lower()
        or "docker-compose" in command_spec.command.lower()
        for command_spec in command_specs
    )


def _related_config_paths(lab_dir: Path) -> list[Path]:
    return [
        lab_dir / "docker-compose.yaml",
        lab_dir / "specmatic.yaml",
        lab_dir / "run-suite-config.yaml",
    ]


def warm_docker_images(
    readme_paths: Sequence[Path],
    timeout_seconds: float = DOCKER_WARMUP_TIMEOUT_SECONDS,
    on_result=None,
) -> list[DockerWarmupResult]:
    results: list[DockerWarmupResult] = []

    for lab_dir in _docker_compose_lab_dirs(readme_paths):
        if on_result is not None and not results:
            print("===== Docker Warmup =====")
        try:
            completed = subprocess.run(
                ["docker", "compose", "pull", "--ignore-buildable"],
                cwd=str(lab_dir),
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            result = DockerWarmupResult(
                lab_name=lab_dir.name,
                passed=False,
                detail=f"timed out after {int(timeout_seconds)} seconds",
            )
            results.append(result)
            if on_result is not None:
                on_result(result)
            continue
        except OSError as exc:
            result = DockerWarmupResult(
                lab_name=lab_dir.name,
                passed=False,
                detail=str(exc),
            )
            results.append(result)
            if on_result is not None:
                on_result(result)
            continue

        if completed.returncode == 0:
            result = DockerWarmupResult(lab_name=lab_dir.name, passed=True)
            results.append(result)
            if on_result is not None:
                on_result(result)
            continue

        error_output = completed.stderr.strip() or completed.stdout.strip() or "docker compose pull failed"
        result = DockerWarmupResult(
            lab_name=lab_dir.name,
            passed=False,
            detail=error_output,
        )
        results.append(result)
        if on_result is not None:
            on_result(result)

    return results


def _docker_compose_lab_dirs(readme_paths: Sequence[Path]) -> list[Path]:
    lab_dirs: list[Path] = []
    seen: set[Path] = set()

    for readme_path in readme_paths:
        lab_dir = readme_path.parent
        docker_compose_path = lab_dir / "docker-compose.yaml"
        if lab_dir in seen or not docker_compose_path.is_file():
            continue
        if not _readme_uses_docker_compose(readme_path):
            continue
        seen.add(lab_dir)
        lab_dirs.append(lab_dir)

    return lab_dirs


def run_preflight(
    readme_paths: Sequence[Path],
    requirements: PreflightRequirements | None = None,
    on_result=None,
) -> list[PreflightCheckResult]:
    requirements = requirements or determine_preflight_requirements(readme_paths)
    if not requirements.any_required:
        return []

    results: list[PreflightCheckResult] = []
    repo_root = Path(__file__).resolve().parent
    license_path = repo_root / "license.txt"

    if requirements.docker_cli:
        result = _run_preflight_command(
            name="docker",
            command=["docker", "--version"],
            failure_detail="docker CLI is not available",
            suggestion="Install Docker and make sure `docker` is on PATH.",
        )
        results.append(result)
        if on_result is not None:
            on_result(result)

    docker_ready = not results or results[-1].passed
    if requirements.docker_compose:
        result = _run_preflight_command(
            name="docker compose",
            command=["docker", "compose", "version"],
            failure_detail="docker compose is not available",
            suggestion="Install a Docker version that includes `docker compose`.",
        )
        results.append(result)
        if on_result is not None:
            on_result(result)
        docker_ready = docker_ready and results[-1].passed

    if requirements.docker_cli and docker_ready:
        result = _run_preflight_command(
            name="docker daemon",
            command=["docker", "info"],
            failure_detail="Docker daemon is not reachable",
            suggestion="Start Docker Desktop or the Docker daemon, then rerun the validator.",
        )
        results.append(result)
        if on_result is not None:
            on_result(result)
        docker_ready = docker_ready and results[-1].passed
    elif requirements.docker_cli:
        result = PreflightCheckResult(
            name="docker daemon",
            passed=False,
            skipped=True,
            detail="skipped because Docker CLI/Compose is unavailable",
            suggestion="Fix the Docker installation first.",
        )
        results.append(result)
        if on_result is not None:
            on_result(result)

    if requirements.license_validation:
        if license_path.is_file():
            result = PreflightCheckResult(name="specmatic license file exists", passed=True)
        else:
            result = PreflightCheckResult(
                name="specmatic license file exists",
                passed=False,
                detail=f"missing {license_path}",
                suggestion="Add a valid `license.txt` at the labs repo root.",
            )
        results.append(result)
        if on_result is not None:
            on_result(result)

        if docker_ready and license_path.is_file():
            result = _validate_specmatic_license(repo_root)
        else:
            result = PreflightCheckResult(
                name="specmatic license validation",
                passed=False,
                skipped=True,
                detail="skipped because Docker or the license file is unavailable",
                suggestion="Fix Docker access and the license file, then rerun the validator.",
            )
        results.append(result)
        if on_result is not None:
            on_result(result)

    if requirements.remote_contract_access:
        result = _run_preflight_command(
            name="labs-contracts access",
            command=[
                "git",
                "ls-remote",
                "--exit-code",
                "https://github.com/specmatic/labs-contracts.git",
                "HEAD",
            ],
            failure_detail="cannot reach github.com/specmatic/labs-contracts.git",
            suggestion="Check network access to GitHub, then rerun the validator.",
        )
        results.append(result)
        if on_result is not None:
            on_result(result)

    return results


def _run_preflight_command(
    *,
    name: str,
    command: Sequence[str],
    failure_detail: str,
    suggestion: str,
    cwd: Path | None = None,
) -> PreflightCheckResult:
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return PreflightCheckResult(
            name=name,
            passed=False,
            detail=f"{failure_detail}: {exc}",
            suggestion=suggestion,
        )

    if completed.returncode == 0:
        return PreflightCheckResult(name=name, passed=True)

    error_output = completed.stderr.strip() or completed.stdout.strip() or failure_detail
    return PreflightCheckResult(
        name=name,
        passed=False,
        detail=error_output,
        suggestion=suggestion,
    )


def _validate_specmatic_license(repo_root: Path) -> PreflightCheckResult:
    completed = subprocess.run(
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
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)

    loaded_expected_license = "initialized from /specmatic/specmatic-license.txt" in output
    expired_license = "is expired" in output
    fell_back_to_default = "initialized from jar:file:" in output

    if completed.returncode == 0 and loaded_expected_license and not expired_license and not fell_back_to_default:
        return PreflightCheckResult(name="specmatic license validation", passed=True)

    return PreflightCheckResult(
        name="specmatic license validation",
        passed=False,
        detail=output or "Specmatic license validation failed.",
        suggestion="Replace `license.txt` with a valid, unexpired Specmatic license.",
    )


def print_preflight_results(results: Sequence[PreflightCheckResult]) -> None:
    if not results:
        return

    print("===== Preflight =====")
    for result in results:
        _print_preflight_result(result)


def print_docker_warmup_results(results: Sequence[DockerWarmupResult]) -> None:
    if not results:
        return

    print("===== Docker Warmup =====")
    for result in results:
        _print_docker_warmup_result(result)


def _print_preflight_result(result: PreflightCheckResult) -> None:
    if result.skipped:
        status = "SKIP"
    else:
        status = "PASS" if result.passed else "FAIL"
    if result.detail:
        print(f"{status} {result.name}: {result.detail}")
    else:
        print(f"{status} {result.name}")
    if (not result.passed or result.skipped) and result.suggestion:
        print(f"  Fix: {result.suggestion}")


def _print_docker_warmup_result(result: DockerWarmupResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    if result.detail:
        print(f"{status} {result.lab_name}: {result.detail}")
    else:
        print(f"{status} {result.lab_name}")


def print_command_mapping(command_specs: Sequence[CommandSpec]) -> None:
    separator = _style("=" * 72, ANSI_DIM)

    for index, command_spec in enumerate(command_specs, start=1):
        print(separator)
        print(_style(f"Command #{index}", ANSI_BOLD, ANSI_CYAN))
        print(
            _style("Shell", ANSI_BOLD, ANSI_YELLOW)
            + f"  {_style(f'(expected terminaloutput blocks: {len(command_spec.expected_outputs)})', ANSI_DIM)}"
        )
        _print_indented_block(command_spec.command)
        for output_index, expected_output in enumerate(command_spec.expected_outputs, start=1):
            print()
            print(_style(f"terminaloutput #{output_index}", ANSI_BOLD, ANSI_GREEN))
            _print_indented_block(expected_output)
        if not command_spec.expected_outputs:
            print()
            print(_style("terminaloutput  none", ANSI_DIM))
        print()
    if command_specs:
        print(separator)


def print_dry_run(command_specs: Sequence[CommandSpec]) -> None:
    print_command_mapping(command_specs)


def _print_indented_block(content: str) -> None:
    for line in content.rstrip("\n").splitlines():
        print(f"  {line}")


def snapshot_repo_state(cwd: Path) -> RepoSnapshot | None:
    repo_root = _get_repo_root(cwd)
    if repo_root is None:
        return None

    scope = cwd.resolve().relative_to(repo_root)

    return RepoSnapshot(
        repo_root=repo_root,
        scope=scope,
        tracked_dirty=_git_path_set(
            repo_root,
            ["git", "status", "--porcelain=v1", "--untracked-files=no", "-z", "--", str(scope)],
        ),
        untracked=_git_path_set(
            repo_root,
            ["git", "ls-files", "-o", "--exclude-standard", "-z", "--", str(scope)],
        ),
    )


def reset_lab_changes(cwd: Path, baseline: RepoSnapshot | None) -> ResetSummary:
    if baseline is None:
        return ResetSummary(restored=[], removed=[])

    current_snapshot = snapshot_repo_state(cwd)
    if current_snapshot is None:
        return ResetSummary(restored=[], removed=[])

    paths_to_restore = sorted(current_snapshot.tracked_dirty - baseline.tracked_dirty)
    paths_to_remove = sorted(current_snapshot.untracked - baseline.untracked)

    if paths_to_restore:
        _run_git_command(
            baseline.repo_root,
            ["git", "restore", "--worktree", "--source=HEAD", "--", *[str(path) for path in paths_to_restore]],
        )

    removed: list[Path] = []
    for path in paths_to_remove:
        absolute_path = baseline.repo_root / path
        if not absolute_path.exists():
            continue
        if absolute_path.is_dir():
            shutil.rmtree(absolute_path)
        else:
            absolute_path.unlink()
        removed.append(path)

    return ResetSummary(restored=paths_to_restore, removed=removed)


def print_reset_summary(reset_summary: ResetSummary) -> None:
    if not reset_summary.restored and not reset_summary.removed:
        return

    print(
        "RESET "
        f"(restored: {len(reset_summary.restored)}, removed: {len(reset_summary.removed)})"
    )


def print_run_summary(summary: ValidationRunSummary, total_commands: int) -> None:
    for result in summary.results:
        if result.skipped:
            print(
                f"SKIP command #{result.index} "
                f"(contains both 'docker' and 'studio')"
            )
        else:
            status = "FAIL" if summary.failed_index == result.index else "PASS"
            print(
                f"{status} command #{result.index} (exit {result.returncode}, "
                f"expected blocks: {len(result.expected_outputs)})"
            )

    for index in range(len(summary.results) + 1, total_commands + 1):
        print(f"SKIP command #{index}")


def _format_duration(duration_seconds: float) -> str:
    if duration_seconds < 60:
        return f"{duration_seconds:.2f}s"

    minutes, seconds = divmod(duration_seconds, 60)
    if duration_seconds < 3600:
        return f"{int(minutes)}m {seconds:.2f}s"

    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"


def total_commands_skipped(summary: ValidationRunSummary, total_commands: int) -> int:
    executed_skips = sum(1 for result in summary.results if result.skipped)
    remaining_skips = total_commands - len(summary.results)
    return executed_skips + remaining_skips


def print_multi_lab_summary(
    passed_labs: Sequence[LabExecutionResult],
    failed_labs: Sequence[LabExecutionResult],
    dry_run: bool = False,
) -> None:
    print("===== Summary =====")
    if dry_run:
        dry_run_labs = [*passed_labs, *failed_labs]
        print(f"DRY RUN labs: {len(dry_run_labs)}")
        print()
        _print_summary_table(
            rows=[
                (
                    lab.name,
                    "DRY RUN",
                    _format_duration(lab.duration_seconds),
                    str(lab.total_commands),
                    "-",
                )
                for lab in dry_run_labs
            ],
            validated_header="Commands",
        )
        return

    print(f"PASS labs: {len(passed_labs)}")
    print(f"FAIL labs: {len(failed_labs)}")
    print()
    _print_summary_table(
        rows=[
            (
                lab.name,
                "PASS",
                _format_duration(lab.duration_seconds),
                f"{lab.validated_commands}/{lab.total_commands}",
                str(lab.skipped_commands),
            )
            for lab in passed_labs
        ]
        + [
            (
                lab.name,
                "FAIL",
                _format_duration(lab.duration_seconds),
                f"{lab.validated_commands}/{lab.total_commands}",
                str(lab.skipped_commands),
            )
            for lab in failed_labs
        ]
    )


def _print_summary_table(
    *,
    rows: Sequence[tuple[str, str, str, str, str]],
    validated_header: str = "Validated",
) -> None:
    if not rows:
        return

    headers = ("Lab", "Status", "Duration", validated_header, "Skipped")
    col_widths = [
        max(len(headers[0]), *(len(row[0]) for row in rows)),
        max(len(headers[1]), *(len(row[1]) for row in rows)),
        max(len(headers[2]), *(len(row[2]) for row in rows)),
        max(len(headers[3]), *(len(row[3]) for row in rows)),
        max(len(headers[4]), *(len(row[4]) for row in rows)),
    ]

    def format_row(columns: Sequence[str]) -> str:
        return (
            f"{columns[0]:<{col_widths[0]}}  "
            f"{columns[1]:<{col_widths[1]}}  "
            f"{columns[2]:>{col_widths[2]}}  "
            f"{columns[3]:>{col_widths[3]}}  "
            f"{columns[4]:>{col_widths[4]}}"
        )

    print(format_row(headers))
    print(
        f"{'-' * col_widths[0]}  "
        f"{'-' * col_widths[1]}  "
        f"{'-' * col_widths[2]}  "
        f"{'-' * col_widths[3]}  "
        f"{'-' * col_widths[4]}"
    )
    for row in rows:
        print(format_row(row))


def _get_repo_root(cwd: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return Path(completed.stdout.strip())


def _git_path_set(cwd: Path, command: list[str]) -> set[Path]:
    completed = _run_git_command(cwd, command)
    if command[1:3] == ["status", "--porcelain=v1"]:
        return _parse_status_paths(completed.stdout)
    return {Path(path) for path in completed.stdout.split("\0") if path}


def _parse_status_paths(output: str) -> set[Path]:
    paths: set[Path] = set()
    for entry in output.split("\0"):
        if entry and len(entry) >= 4:
            paths.add(Path(entry[3:]))
    return paths


def _run_git_command(cwd: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "unknown git error"
        raise GitInteractionError(f"Git command failed: {' '.join(command)}\n{stderr}")
    return completed


if __name__ == "__main__":
    sys.exit(main())
