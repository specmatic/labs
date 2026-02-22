# Studio Lab: Response Templating via Direct Substitution and Data Lookup

## Objective
Use response templating in Specmatic mocks to make mock responses deterministic and correlated with request data.

## Problem Statement

In service virtualization, static mock responses are often too rigid for real workflows. Teams need mocks that return responses based on incoming request data (for example, echoing identifiers) and also derive related fields from business mappings (for example, department to designation). Without this, contract tests become brittle, scenarios are unrealistic, and teams spend time creating many near-duplicate examples.
This lab solves that by teaching how to build dynamic, data-aware mock responses computed from request values at runtime using Direct Substitution and Data Lookup in Specmatic.

Participants will:

* Implement Direct Substitution to capture request values into variables and inject them into responses.
* Implement Data Lookup to map a request value (like department) to dependent response fields (like designation) using a lookup object.
* Understand when to use substitution vs lookup, and how both improve contract-test realism with minimal example duplication.
* By the end, participants will be able to design mocks that are deterministic, reusable, and closer to production-like behavior.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/response-templating`.

## Files in this lab
- `specs/simple-openapi-spec.yaml`: OpenAPI contract.
- `examples/test/*.json`: Contract tests (do not edit these in this lab).
- `examples/mock/*.json`: Mock examples (you will edit these).
- `specmatic.yaml`: Specmatic test/mock configuration.

## Reference
- Correlated request/response values (Direct Substitution + Data Lookup): [https://docs.specmatic.io/contract_driven_development/service_virtualization#correlated-request-and-response-values](https://docs.specmatic.io/contract_driven_development/service_virtualization#correlated-request-and-response-values)

## Lab Rules
- Do not edit `specs/simple-openapi-spec.yaml`.
- Do not edit files under `examples/test/`.
- Apply all fixes only in files under `examples/mock/`.

## 1. Run baseline test (intentional failure)
```shell
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 4, Successes: 1, Failures: 3, Errors: 0
```

Clean up:
```shell
docker compose down -v
```

### What is failing now
- `POST /orders -> 201`: response `productid` and `count` do not match request values.
- `GET /findAvailableProducts (type=book)`: response `name` mismatch (`Harry Potter` vs expected `Larry Potter`).
- `GET /findAvailableProducts (type=gadget)`: response values are not deterministically mapped for gadget scenario.

## 2. Open Studio (Optional)
```shell
docker run --rm \
  --name studio \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  -p 9000:9000 \
  -p 9001:9001 \
  specmatic/enterprise:latest \
  studio
```
Windows (PowerShell/CMD) single-line:
```shell
docker run --rm --name studio -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro -p 9000:9000 -p 9001:9001 specmatic/enterprise:latest studio
```
Open Studio at `http://127.0.0.1:9000/_specmatic/studio`.

## 3. Task A: Fix order response using Direct Substitution
Edit:
- `examples/mock/test_accepted_order_request.json`

Change response templating so:
- `http-response.body.productid` is copied from `http-request.body.productid`.
- `http-response.body.count` is copied from `http-request.body.count`.

Keep `id` as-is.

### Checkpoint after Task A
Run:
```shell
docker compose up test --abort-on-container-exit
```
Expected checkpoint output:
```terminaloutput
Tests run: 4, Successes: 2, Failures: 2, Errors: 0
```
Clean up:
```shell
docker compose down -v
```

## 4. Task B: Fix product search using Data Lookup
Edit:
- `examples/mock/test_find_available_products_book_200.json`

Configure lookup logic based on request query `type` so that:
- for `type=book` return response values matching test expectation (`id=1`, `name=Larry Potter`, `type=book`, `inventory=100`, `createdOn=2026-02-15`)
- for `type=gadget` return response values matching test expectation (`id=2`, `name=iPhone`, `type=gadget`, `inventory=500`, `createdOn` as valid date)

Note:
- You can keep this as one lookup-driven mock example instead of creating duplicate mock files.

## 5. Final verification
Run:
```shell
docker compose up test --abort-on-container-exit
```

Expected final output:
```terminaloutput
Tests run: 4, Successes: 4, Failures: 0, Errors: 0
```

Clean up:
```shell
docker compose down -v
```

## Pass Criteria
- Baseline run fails with `1` success and `3` failures.
- After Task A, run shows `2` successes and `2` failures.
- After Task B, run shows `4` successes and `0` failures.

## Why this lab matters
- Direct Substitution is best when response fields should echo request values.
- Data Lookup is best when response values should come from a deterministic business mapping.
