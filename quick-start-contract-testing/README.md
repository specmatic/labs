# Quick Start: Contract Testing Against a Real Service

This lab helps you learn one thing quickly: run Specmatic contract tests against a real service implementation.

## Goal
Your goal is to make the contract test pass by fixing the service implementation.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker Engine running
- Port `8080` available

## Files in this lab
- `specs/service.yaml` - OpenAPI contract (source of truth for this lab)
- `service/` - Tiny Python service implementation (intentionally has one mismatch)
- `docker-compose.yaml` - Runs the service and Specmatic contract test

## Exercise Rule
Do not edit `specs/service.yaml` in this lab.

## Part A: Run the contract test (expected to fail)
From this folder, run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected result:
- The contract test fails because the service response does not match the contract.
- The mismatch is in `GET /pets/{petid}` response body.

Stop and clean up:

```shell
docker compose down
```

## Part B: Fix the service
Open `service/server.py` and locate the `GET /pets/{petid}` response.

It currently returns `petType`.
Update it to return `type` so the response matches `specs/service.yaml`.

## Part C: Re-run tests (expected to pass)
Run again:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected result:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Stop and clean up:

```shell
docker compose down
```

## Run the same test in Studio
Start only the service:

```shell
docker compose up --build petstore
```

You should see:

```terminaloutput
Attaching to quick-start-petstore
```

In a separate terminal, start Studio:

```shell
docker run --rm --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```

Open [Specmatic Studio](http://localhost:9000/_specmatic/studio), then:
1. From the left panel, open `specs/service.yaml`.
2. Go to the **Test** tab.
3. Set URL to `http://localhost:8080`.
4. Click **Run**.

You should see the same failure before the fix and success after the fix.

Stop Studio by pressing `Ctrl+C` in the terminal where you started it.

Stop service:

```shell
docker compose down
```

## What you learned
- Contract testing validates a real implementation against the contract.
- The contract is the agreed behavior; your service implementation must conform to it.
- Specmatic gives actionable mismatch feedback to help fix implementation gaps.
