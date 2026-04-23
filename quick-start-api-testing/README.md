---
lab_schema: v2
reports:
  ctrf: true
  html: true
  readme_summary: true
  console_summary: true
---
# Quick Start API Testing Lab

## Objective
Use Specmatic matchers in API tests so the examples assert exact business values where needed, while still staying resilient to valid runtime variation.

## Why this lab matters
Real services often return a mix of stable and unstable values:
- one field may always be the same
- one field may legitimately be one of several allowed values
- one field may be generated as a fresh timestamp
- one field may follow a format without being fixed to one exact value

This lab shows how to express each of those expectations with the right matcher on the test side.

![API Testing](assets/api-testing.gif)

## Time required
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in the directory `labs/quick-start-api-testing`.

## Architecture
- `service/server.py` runs a small Python verification service.
- `.specmatic/repos/labs-contracts/openapi/verification/verification-api.yaml` defines the contract loaded by `specmatic.yaml`.
- `specmatic.yaml` points Specmatic at the contract and the external test examples.
- `examples/*.json` contains the test requests and expected responses that you will update in this lab.

## Files in this lab
- `.specmatic/repos/labs-contracts/openapi/verification/verification-api.yaml` - OpenAPI contract for the verification service.
- `service/server.py` - Python service implementation that already satisfies the contract.
- `examples/test_finance_user_11.json` - test example you will fix using `pattern`.
- `examples/test_support_user_55.json` - test example you will fix using `dataType` and `pattern`.
- `docker-compose.yaml` - runs provider and contract tests.
- `specmatic.yaml` - Specmatic configuration.

## Lab Rules
- Do not edit the specs in `.specmatic/repos/labs-contracts/openapi/verification/verification-api.yaml`.
- Do not edit `service/server.py`.
- Do not edit `docker-compose.yaml`.
- Edit only these files:
  - `examples/test_finance_user_11.json`
  - `examples/test_support_user_55.json`

## Specmatic references
- Matchers: [https://docs.specmatic.io/features/matchers](https://docs.specmatic.io/features/matchers)
- Contract testing overview: [https://docs.specmatic.io/documentation/contract_testing.html](https://docs.specmatic.io/documentation/contract_testing.html)

## Lab Implementation Phases

### Baseline Phase
<!--
phase-meta
id: baseline
kind: baseline
validates_test_counts: true
expected_reports:
  readme_summary: true
  console_summary: true
  ctrf: true
  html: true
os_scope: all
-->
The verification service is already contract-compliant. The intentional problem is in the test examples:
- `handledBy` is always `verification-service`
- `decision` may be `approved` or `verified`
- `processedOn` is generated at runtime
- `referenceCode` follows the pattern `VRF-######`

Run:

```shell
docker compose up api-test --build --abort-on-container-exit
```

Expected output:

```terminaloutput
Tests run: 4, Successes: 2, Failures: 2, Errors: 0
```

Why the baseline fails:
- `test_finance_user_11.json` expects `decision` to be exactly `approved`, but the service may return `approved` or `verified` for that request.
- `test_support_user_55.json` expects one hardcoded date and one exact reference code, but the service generates fresh valid values every time.

Clean up:

```shell
docker compose down -v
```

Expected cleanup output:

```terminaloutput
Container quick-start-api-testing-api-test-1  Removed
Container quick-start-api-testing-service-1  Removed
Network quick-start-api-testing_default  Removed
```

### Intermediate Phase: Task A
<!--
phase-meta
id: task-a
kind: intermediate
validates_test_counts: true
expected_reports:
  readme_summary: true
  console_summary: true
  ctrf: true
  html: true
os_scope: all
-->
Edit `examples/test_finance_user_11.json`.

In `http-response.body`, change:
- `decision` from `$match(exact: approved)` to `$match(pattern: approved|verified)`

Do not change any other fields.

Re-run:

```shell
docker compose up api-test --build --abort-on-container-exit
```

Expected output:

```terminaloutput
Tests run: 4, Successes: 3, Failures: 1, Errors: 0
```

Clean up:

```shell
docker compose down -v
```

Expected cleanup output:

```terminaloutput
Container quick-start-api-testing-api-test-1  Removed
Container quick-start-api-testing-service-1  Removed
Network quick-start-api-testing_default  Removed
```

### Final Phase
<!--
phase-meta
id: final
kind: final
validates_test_counts: true
expected_reports:
  readme_summary: true
  console_summary: true
  ctrf: true
  html: true
os_scope: all
-->
Edit `examples/test_support_user_55.json`.

In `http-response.body`, change:
- `processedOn` from the exact date to `$match(dataType: date)`
- `referenceCode` from the exact code to `$match(pattern: VRF-[0-9]{6})`

Keep `handledBy` and `decision` as exact matches.

Run:

```shell
docker compose up api-test --build --abort-on-container-exit
```

Expected output:

```terminaloutput
Tests run: 4, Successes: 4, Failures: 0, Errors: 0
```

Clean up:

```shell
docker compose down -v
```

Expected cleanup output:

```terminaloutput
Container quick-start-api-testing-api-test-1  Removed
Container quick-start-api-testing-service-1  Removed
Network quick-start-api-testing_default  Removed
```

## Pass Criteria
- Baseline run shows `2` failures.
- After Task A, only `1` failure remains.
- After Task B, all `4` tests pass.

## Troubleshooting
- If you get a stale result after changing the test examples, rerun with `--build` and then `docker compose down -v`.
- If all tests pass on the first run, confirm you only edited the two allowed test files and did not save the matcher fixes already.

## Cleanup
Each implementation phase already ends with `docker compose down -v`, so no additional cleanup is required after the final phase.

## What you learned
- `exact` is good when one business value must stay fixed.
- `pattern` is useful when a response may validly be one of several strings or must follow a format.
- `dataType` is useful when the exact value does not matter but the type still does.
- Matchers belong in tests when you want resilient assertions against a real service.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
