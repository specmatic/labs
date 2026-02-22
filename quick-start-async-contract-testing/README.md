# Quick Start Async: Contract Testing Against a Real Event Processor

This lab demonstrates AsyncAPI contract testing against a real provider service.

## Goal
Make async contract tests pass by fixing the provider implementation.

## Prerequisites
- Docker Engine running
- Ports `9092` and `9000` available

## Files in this lab
- `specs/async.yaml` - AsyncAPI contract (source of truth for this lab)
- `service/processor.py` - Tiny Python event processor implementation (intentional mismatch)
- `specmatic.yaml` - Specmatic test configuration for AsyncAPI
- `docker-compose.yaml` - Kafka broker, provider, and contract test runner

## Exercise Rule
Do not edit `specs/async.yaml` in this lab.

## Part A: Run async contract test (expected to fail)
From this folder, run:

```shell
docker compose up --build
```

Expected result:
- Contract test fails due to a mismatch in the provider's response event payload.
- Look for the mismatch on `status` in the output event.

Stop and clean up:

```shell
docker compose down
```

## Part B: Fix the provider
Open [service/processor.py](service/processor.py) and find the response payload in `process_message`.

It currently sets:

```python
"status": "STARTED"
```

Update it to:

```python
"status": "INITIATED"
```

## Part C: Re-run tests (expected to pass)
Run again:

```shell
docker compose up --build
```

Expected result:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Stop and clean up:

```shell
docker compose down
```

## Optional: Run in Studio
Start Studio:

```shell
docker compose --profile studio up studio --build
```

Open [Studio](http://127.0.0.1:9000/_specmatic/studio), open `specmatic.yaml`, and click **Run Suite**.

When done:

```shell
docker compose --profile studio down
```

## What you learned
- Async contract testing validates event-driven behavior against AsyncAPI contracts.
- The contract stays stable while providers evolve to conform.
- Specmatic gives actionable mismatch feedback for event payloads and headers.
