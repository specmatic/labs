# Specmatic Lab: Response Templating via Direct Substitution and Data Lookup

## Objective
Use response templating in Specmatic mocks to make mock responses deterministic and correlated with request data.

## Problem Statement

In service virtualization, static mock responses are often too rigid for real workflows. Consider these common scenarios:

**Example 1: Order Creation**
- Request: `POST /orders` with `{"productid": "ABC123", "count": 5}`
- Static mock always returns: `{"id": 1, "productid": "XYZ789", "count": 10}`
- **Problem**: The response doesn't reflect the actual request data, making tests unrealistic

**Example 2: Product Search**
- Request: `GET /findAvailableProducts?type=book`
- Static mock returns: `{"name": "Harry Potter", "type": "book"}` for all product requests
- **Problem**: No way to return different product details based on the search type

Teams need mocks that:
1. Echo request data back in responses (like returning the same `productid` and `count` that were sent in the order)
2. Use a lookup to derive correlated response fields (like mapping `type=book` to a specific product name, inventory, and date)

This lab teaches **Direct Substitution** (for echoing values) and **Data Lookup** (for input-based mappings) to create dynamic, deterministic mock responses that behave more like real services.

Participants will:

* Implement Direct Substitution to capture request values into variables and inject them into responses.
* Implement Data Lookup to map a request query value (like `type=book`) to a set of correlated response fields (like product name, inventory, and date).
* Understand when to use substitution vs lookup, and how both improve contract-test realism with minimal example duplication.
* By the end, participants will be able to design mocks that are deterministic, reusable, and closer to production-like behavior.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/response-templating`.

## Files in this lab
- `.specmatic/repos/labs-contracts/openapi/response-templating/simple-openapi-spec.yaml`: OpenAPI contract loaded by `specmatic.yaml`.
- `examples/test/*.json`: Contract tests (do not edit these in this lab).
- `examples/mock/*.json`: Mock examples (you will edit these).
- `specmatic.yaml`: Specmatic test/mock configuration.

## Reference
- Correlated request/response values (Direct Substitution + Data Lookup): [https://docs.specmatic.io/contract_driven_development/service_virtualization#correlated-request-and-response-values](https://docs.specmatic.io/contract_driven_development/service_virtualization#correlated-request-and-response-values)

## Lab Rules
- Do not edit the spec in `.specmatic/repos/labs-contracts/openapi/response-templating/simple-openapi-spec.yaml`.
- Do not edit files under `examples/test/`.
- Apply all fixes only in files under `examples/mock/`.

## 1. Run baseline test (intentional failure)
```shell
docker compose up --abort-on-container-exit
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

## 2. Task A: Fix order response using Direct Substitution
Edit:
- `examples/mock/test_accepted_order_request.json`

Change response templating so:
- `http-response.body.productid` is copied from `http-request.body.productid`.
- `http-response.body.count` is copied from `http-request.body.count`.

Keep `id` as-is.

### Checkpoint after Task A
Run:
```shell
docker compose up --abort-on-container-exit
```
Expected checkpoint output:
```terminaloutput
Tests run: 4, Successes: 2, Failures: 2, Errors: 0
```
Clean up:
```shell
docker compose down -v
```

## 3. Task B: Fix product search using Data Lookup
Edit:
- `examples/mock/test_find_available_products_book_200.json`

Configure lookup logic based on request query `type` so that:
- for `type=book` return response values matching test expectation (`id=1`, `name=Larry Potter`, `type=book`, `inventory=100`, `createdOn=2026-02-15`)
- for `type=gadget` return response values matching test expectation (`id=2`, `name=iPhone`, `type=gadget`, `inventory=500`, `createdOn` as valid date)

Note:
- You can keep this as one lookup-driven mock example instead of creating duplicate mock files.

## 4. Final verification
Run:
```shell
docker compose up --abort-on-container-exit
```

Expected final output:
```terminaloutput
Tests run: 4, Successes: 4, Failures: 0, Errors: 0
```

Clean up:
```shell
docker compose down -v
```

## Specmatic Types to OpenAPI Types Mapping
| Specmatic type token | OpenAPI type       | OpenAPI format / note                            |
|----------------------|--------------------|--------------------------------------------------|
| (number)             | number             | double or float                                  |
| (integer)            | integer            |                                                  |
| (boolean)            | boolean            |                                                  |
| (null)               | null               | Only valid in OAS 3.1                            |
| (string)             | string             |                                                  |
| (email)              | string             | email                                            |
| (date)               | string             | date                                             |
| (datetime)           | string             | date-time                                        |
| (time)               | string             | time                                             |
| (uuid)               | string             | uuid                                             |
| (url)                | string             | uri                                              |
| (url-http)           | string             | uri (used by Specmatic to match HTTP urls only)  |
| (url-https)          | string             | uri (used by Specmatic to match HTTPS urls only) |
| (url-path)           | string             | path-style URL constraint                        |
| (anything)           | any                | unconstrained schema ({}-like)                   |
| (anyvalue)           | any non-null value | unconstrained-ish, but intended as "any value"   |

## Pass Criteria
- Baseline run fails with `1` success and `3` failures.
- After Task A, run shows `2` successes and `2` failures.
- After Task B, run shows `4` successes and `0` failures.

## Why this lab matters
- Direct Substitution is best when response fields should echo request values (e.g. returning the same `productid` that was sent).
- Data Lookup is best when response values should come from a deterministic business mapping.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
