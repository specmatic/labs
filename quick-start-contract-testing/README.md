# Quick Start: Contract Testing Against a Real Service

## Objective
Run Specmatic against a real service implementation, see a contract failure, and fix the implementation without changing the contract.

## Why this lab matters
This is the core contract-driven development loop:
1. Keep the contract as source of truth.
2. Run contract tests against the running provider.
3. Use mismatch feedback to fix provider behavior.

If teams do this continuously, contract breaks are caught before release instead of in integration or production.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/quick-start-contract-testing`.
- Port `8080` is available.

## Files in this lab
- `specs/service.yaml` - OpenAPI contract (source of truth for this lab).
- `service/server.py` - Tiny Python service implementation with one intentional mismatch.
- `docker-compose.yaml` - Runs provider (`petstore`) and test runner (`contract-test`).

## Learner task
Make contract tests pass by changing provider response field `petType` to `type` in `service/server.py`.

## Lab Rules
- Do not edit `specs/service.yaml`.
- Do not edit `docker-compose.yaml`.
- Fix only the service implementation in `service/server.py`.

## Specmatic references
- Contract testing overview: [https://docs.specmatic.io/documentation/contract_testing.html](https://docs.specmatic.io/documentation/contract_testing.html)
- Understanding validation rules and mismatch codes: [https://docs.specmatic.io/rules](https://docs.specmatic.io/rules)
- Specmatic Studio: [https://docs.specmatic.io/documentation/studio.html](https://docs.specmatic.io/documentation/studio.html)

## Part A: Baseline run (intentional failure)
Run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 1, Successes: 0, Failures: 1, Errors: 0
```

Expected failure reason:
- Contract requires response field `type`.
- Service currently returns `petType`.
- You may also see `Could not find the Specmatic configuration at path /usr/src/app/specmatic.yaml`.
  In this lab, that message is expected because `contract-test` runs directly with `./specs/service.yaml`.

Clean up:

```shell
docker compose down -v
```

## Part B: Fix the provider implementation
Open `service/server.py`.

In `do_GET()` under `/pets/`, replace:
```python
"petType": "Golden Retriever",
```
with:
```python
"type": "Golden Retriever",
```

Do not change anything else.

## Part C: Re-run tests (expected to pass)
Run:

```shell
docker compose up contract-test --build --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Clean up:

```shell
docker compose down -v
```

## Optional: Run the same check in Studio
Start provider only:

```shell
docker compose up --build petstore
```

In another terminal, start Studio:

```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  -p 9000:9000 \
  -p 9001:9001 \
  specmatic/enterprise:latest \
  studio
```
Windows (PowerShell/CMD) single-line:
```shell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro -p 9000:9000 -p 9001:9001 specmatic/enterprise:latest studio
```

Open [Specmatic Studio](http://127.0.0.1:9000/_specmatic/studio), then:
1. From the left panel, open `specs/service.yaml`.
2. Go to the **Test** tab.
3. Set URL to `http://127.0.0.1:8080`.
4. Click **Run**.

You should observe the same fail-then-pass behavior based on whether `petType` is fixed to `type`.

Stop Studio by pressing `Ctrl+C` in the terminal where you started it.

Stop services:
```shell
docker compose down -v
```

## Pass criteria
- Baseline contract-test run fails with one mismatch.
- After provider fix, contract-test run passes with `1/1` success.

## Common confusion points
- Looking for `service/app.py` instead of `service/server.py`.
- Editing contract instead of provider code.
- Forgetting `--build` after changing service code (can run stale image).
- Using `localhost` instead of `127.0.0.1` in Studio URL on some setups.

## What you learned
- Contract testing validates a real implementation against the contract.
- The contract is the agreed behavior; your service implementation must conform to it.
- Specmatic gives actionable mismatch feedback to help fix implementation gaps.
