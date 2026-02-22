# Quick Start Async: Contract Testing Against a Real Event Processor

This lab shows why async contract testing matters in real teams: producers and consumers often deploy independently, and schema drift in event payloads can break workflows silently. Here, the AsyncAPI contract is the shared source of truth, and Specmatic catches drift before release.

## Objective
Run an async contract test against a real Kafka-based provider, observe the intentional failure, fix the provider implementation, and verify a passing run.

## Time required to complete this lab
10-15 minutes (first run can take longer if Docker images are not cached locally).

## Prerequisites
- Docker Desktop (or Docker Engine + Compose v2) is installed and running.
- You are in `labs/quick-start-async-contract-testing`.
- Port `9092` is free (required for Kafka in this lab).
- Port `9000` is free (required for Studio).

## Files in this lab
- `specs/async.yaml` - AsyncAPI contract (source of truth for this lab)
- `service/processor.py` - Provider implementation with one intentional mismatch
- `specmatic.yaml` - Specmatic async test configuration
- `docker-compose.yaml` - Kafka, provider service, test runner, and optional Studio
- `create-topics.sh` - Kafka topic bootstrap script used by `kafka-init`

## Learner task
Fix the provider so the emitted response event matches the contract's allowed `status` values.

## Lab Rules
- Do not edit: `specs/async.yaml`, `specmatic.yaml`, `docker-compose.yaml`.
- Edit only: `service/processor.py`.
- If your baseline run unexpectedly passes, reset `service/processor.py` so `process_message` returns `"status": "STARTED"` before continuing.

## Architecture mental model (before you run)
- Consumer under test: Specmatic test runner (`contract-test` service).
- Provider under test: Python processor (`provider` service).
- Flow:
  1. Specmatic publishes an event/message to Kafka topic `new-orders`.
  2. Provider consumes that event, transforms payload, and emits to `wip-orders`.
  3. Specmatic validates emitted payload and headers against `specs/async.yaml`.

## Intentional failure (baseline run)
From this folder, run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected failure signal:
- Contract test fails due to a mismatch in the provider's response event payload.
- Failure points to `status`, where actual is `"STARTED"` and expected is one of the enum values in the contract (including `"INITIATED"`).

Then clean up:

```shell
docker compose down -v
```

## Fix path
Open `service/processor.py` and update `process_message`:

From:

```python
"status": "STARTED",
```

To:

```python
"status": "INITIATED",
```

## Pass criteria
Re-run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected pass signal:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Then clean up:

```shell
docker compose down -v
```

## Run the same suite in Studio
Start Studio:

```shell
docker compose --profile studio up studio --build
```

Open [Studio](http://127.0.0.1:9000/_specmatic/studio, load `specmatic.yaml`, and click **Run Suite**.

Stop Studio stack:

```shell
docker compose --profile studio down -v
```

## Troubleshooting (common beginner blockers)
- `port is already allocated`:
  - Free `9092` and `9000`, then retry.
- `kafka-init` fails with shell/script errors on Windows:
  - Ensure shell scripts are checked out with LF line endings (`create-topics.sh` must not contain CRLF).
- Test exits before provider is ready:
  - Re-run once; services are health-gated, but first image pull/startup can be slow.

## What you learned
- Async contract testing validates event-driven behavior against AsyncAPI contracts.
- Contract failures provide precise mismatch diagnostics (rule code + field path).
- Keeping the contract stable while fixing provider behavior is a practical producer-side workflow.
- Specmatic gives actionable mismatch feedback for event payloads and headers.
