# API Resiliency Testing with Specmatic

Resiliency matters, and yet we still underestimate how fragile the digital world is. A single API failure can cascade across industries: flights delayed, nurses locked out of medication charts, government services unavailable. Recent incidents include a Crowdstrike outage that caused widespread disruption, a Google outage in June 2025 triggered by a null pointer exception, Cloudflare incidents where a frontend retry loop overwhelmed tenant services, and a Tesla API outage that left owners unable to open their cars.

At its core, API resiliency testing is about ensuring services are predictable and durable under adverse conditions. It is not just checking happy paths, Specmatic verifies both degraded response and recovery. Resiliency testing spans a spectrum of approaches designed to expose weaknesses before they fail in production.

## Objective
Learn how to test two resilience behaviors when a downstream dependency is not responsive:
- Load shedding pattern: return `429 Too Many Requests` when product-search load should be shed
- Async Create: return `202 Accepted` when product creation is accepted but not completed yet

## Why this lab matters
Time to time downstream services might experience issue, however these need to be handled gracefully by your service and should not surface as generic timeouts or `500`s.

In this lab, the contract is already the source of truth:
- `GET /findAvailableProducts` should return `429` with `Retry-After` when the downstream product API times out.
- `POST /products` should return `202 Accepted` with a monitor link when the downstream create call is taking time.

Your job is to test the service under test (BFF) matches those resilience expectations by simulating downstream delays through the downstream mock examples.

## Time required to complete this lab
15-20 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/api-resiliency-testing`.
- Ports `8080`, `9000`, and `9001` are available.

## Architecture
- `suite` is the Specmatic contract-test runner that starts dependency mocks and executes the tests.
- `order-bff` is the system under test on port `8080`.
- the dependency mocks are generated from shared contracts in `labs-contracts` (`common/openapi/order-api/api_order_v5.yaml` and `common/asyncapi/product-audits/kafka.yaml`) by the `suite` service.
- The BFF contract under test is pulled from `labs-contracts` (`openapi/order-bff-resiliency/product_search_bff_v6.yaml`).
- You will edit only downstream mock examples in `examples/order-service/`.

## Files in this lab
- `.specmatic/repos/labs-contracts/openapi/order-bff-resiliency/product_search_bff_v6.yaml` - BFF contract under test after `specmatic.yaml` checks out the contracts repo.
- `.specmatic/repos/labs-contracts/common/openapi/order-api/api_order_v5.yaml` - downstream product API contract used for mocking.
- `examples/bff/test_products_too_many_requests.json` - test expecting `429`.
- `examples/bff/test_accepted_product_request.json` - test expecting `202`.
- `examples/order-service/stub_products_200.json` - healthy downstream search stub.
- `examples/order-service/stub_product_201.json` - healthy downstream create stub.
- `examples/order-service/stub_timeout_get_products.json` - matching downstream search example that is missing the delay needed to trigger load shedding.
- `examples/order-service/stub_timeout_post_product.json` - matching downstream create example that is missing the delay needed to trigger `202 Accepted`.

## Learner task
1. Run the baseline and observe two failures.
2. Fix `examples/order-service/stub_timeout_get_products.json` so the `429` test passes.
3. Re-run and confirm only the `202` test is still failing.
4. Fix `examples/order-service/stub_timeout_post_product.json` so the `202` test passes.
5. Enable `schemaResiliencyTests: all` and observe the extra `202` failures.
6. Generalize `examples/order-service/stub_timeout_post_product.json` with `value:each` matchers.
7. Re-run and confirm the full suite passes.

## Lab Rules
- Do not edit the specs pulled from `labs-contracts` in this lab.
- Do not edit files under `examples/bff/`.
- Do not edit `docker-compose.yaml`.
- Edit only:
  - `specmatic.yaml`
  - `examples/order-service/stub_timeout_get_products.json`
  - `examples/order-service/stub_timeout_post_product.json`

## Specmatic references
- `429` resilience demo: [When dependencies timeout, does your API shed load with 429 responses?](https://specmatic.io/demonstration/when-dependencies-timeout-does-your-api-shed-load-with-429-responses/)
- `202` resilience demo: [When downstream services lag, does your API gracefully accept with 202 responses?](https://specmatic.io/demonstration/when-downstream-services-lag-does-your-api-gracefully-accept-with-202-responses/)
- Contract testing docs: [https://docs.specmatic.io/documentation/contract_tests.html](https://docs.specmatic.io/documentation/contract_tests.html)

## Baseline run (intentional failure)
Run:

```shell
docker compose --profile test up --abort-on-container-exit
```

Expected baseline result:

```terminaloutput
Tests run: 5, Successes: 3, Failures: 2, Errors: 0
```

The two failing scenarios should be:
- `GET /findAvailableProducts -> 429` from `test_products_too_many_requests.json`
- `POST /products -> 202` from `test_accepted_product_request.json`

Why they fail:
- `stub_timeout_get_products.json` matches the search request, but it does not delay the downstream response, so the BFF gets a normal `200` instead of shedding load with `429`.
- `stub_timeout_post_product.json` matches the create request, but it does not delay the downstream response, so the BFF completes normally with `201` instead of returning `202 Accepted`.
- In this lab, the delay must be `transient` because Specmatic also verifies recovery: once the downstream service is responsive again, the response should go back to normal.

Clean up:

```shell
docker compose --profile test down -v
```

## Task A: Add a transient delay for the `429` scenario
Open `examples/order-service/stub_timeout_get_products.json`.

It already matches the downstream search request that should trigger load shedding. Add:
- `"transient": true`
- `"delay-in-seconds": 2`

Keep:
- header `pageSize` as `20`
- query `type` as exact value `other` with `times:2`
- query `from-date` as `2025-11-01`
- query `to-date` as `2025-11-15`
- the `200 OK` downstream response body

Re-run:

```shell
docker compose --profile test up --abort-on-container-exit
```

Expected checkpoint result:

```terminaloutput
Tests run: 5, Successes: 4, Failures: 1, Errors: 0
```

At this point:
- the `429` scenario passes
- the `202` scenario still fails

Clean up:

```shell
docker compose --profile test down -v
```

## Task B: Add a transient delay for the `202` scenario
Open `examples/order-service/stub_timeout_post_product.json`.

It already matches the delayed create-product request. Add:
- `"transient": true`
- `"delay-in-seconds": 2`

Keep:
- request body `name` as `UniqueName`
- request body `type` as `book`
- request body `inventory` as `9`
- the existing header matchers
- the downstream `201 Created` response

Re-run:

```shell
docker compose --profile test up --abort-on-container-exit
```

Expected checkpoint result:

```terminaloutput
Tests run: 5, Successes: 5, Failures: 0, Errors: 0
```

At this point:
- the baseline `429` and `202` resilience flow passes
- the lab is still running with `schemaResiliencyTests: none`

Clean up:

```shell
docker compose --profile test down -v
```

## Task C: Enable full schema resiliency for `202`
Open `specmatic.yaml` and change:

```yaml
schemaResiliencyTests: none
```

to:

```yaml
schemaResiliencyTests: all
```

Re-run:

```shell
docker compose --profile test up --abort-on-container-exit
```

What changes:
- the `429` scenario continues to work
- one `202` scenario still passes
- additional generated `POST /products -> 202` requests now appear
- those extra `202` scenarios fail because `stub_timeout_post_product.json` is hard-coded to only one request shape:
  - `name: UniqueName`
  - `type: book`
  - `inventory: 9`

Expected failure direction:
- the suite now reports multiple `POST /products -> 202` failures
- one concrete `202` example still passes
- the new failures come from additional valid request variations generated from the contract

Expected Task C checkpoint result before the matcher fix:

```terminaloutput
Tests run: 249, Successes: 236, Failures:13, Errors:0
```

Why this is useful:
- this is closer to real-world resiliency testing
- Specmatic is not only checking one example anymore
- it is generating valid request variations and expecting the same graceful `202` behavior across them

What is happening under the hood:
- your transient timeout example currently matches only one exact request:
  - `name: UniqueName`
  - `type: book`
  - `inventory: 9`
- with `schemaResiliencyTests: all`, Specmatic generates more valid `POST /products` requests from the contract
- those generated requests still satisfy the API contract, so the BFF is expected to handle them gracefully as well
- but the transient timeout example no longer matches when `type` or `inventory` changes
- when that timeout example does not match, Specmatic falls back to the normal downstream success example, so the BFF receives a fast `201 Created`
- because the downstream did not time out, the BFF returns `201` instead of `202`, and the generated resiliency tests fail

This is also why the transient behavior matters:
- Specmatic is not only checking the degraded path
- it also checks recovery
- the timeout example should apply while the transient delay is active, and then the downstream should go back to normal responses afterward
- this makes the lab more realistic than testing a permanent failure

To fix this, update `examples/order-service/stub_timeout_post_product.json` so the request body becomes:

```json
"body": {
  "name": "UniqueName",
  "type": "$match(dataType:ProductType, value:each, times:1)",
  "inventory": "$match(dataType:ProductInventory, value:each, times:1)"
}
```

Why `value:each` is the right matcher here:
- `value:each` tracks matcher exhaustion separately for each distinct value
- that means each valid `type` value gets its own one-time transient timeout match
- each valid `inventory` value also gets its own one-time transient timeout match
- this lets the same timeout example work for unique valid request variations generated by `schemaResiliencyTests: all`
- a hard-coded value like `type: book` only works for one request shape, but `value:each` scales the transient behavior across the generated valid inputs

Specmatic documentation for this matcher behavior:
- [Matchers: step-by-step example for `value: each`](https://docs.specmatic.io/features/matchers#step-by-step-example-for-value-each)

Keep:
- `"transient": true`
- `"delay-in-seconds": 2`
- the existing header matchers
- the downstream `201 Created` response

Re-run again:

```shell
docker compose --profile test up --abort-on-container-exit
```

Expected outcome:
- the additional generated `202` scenarios now pass
- the lab still verifies both degraded behavior and recovery after the transient timeout

Final expected result:

```terminaloutput
Tests run: 211, Successes: 211, Failures: 0, Errors: 0
```

Clean up:

```shell
docker compose --profile test down -v
```

## Run the same flow in Studio
Start Studio:

```shell
docker compose --profile studio up --build
```

Open [http://127.0.0.1:9000/_specmatic/studio](http://127.0.0.1:9000/_specmatic/studio).

Then:
1. Open `specmatic.yaml`.
2. Click **Run Suite**.
3. Observe the same two failures in the baseline state.
4. Fix `stub_timeout_get_products.json` and rerun.
5. Confirm only the `202` scenario still fails.
6. Fix `stub_timeout_post_product.json` and rerun.
7. Change `schemaResiliencyTests` to `all`.
8. Observe the extra generated `202` failures.
9. Update `stub_timeout_post_product.json` to use `value:each` matchers.
10. Rerun and confirm the full suite passes.

Stop Studio:

```shell
docker compose --profile studio down -v
```

## Troubleshooting
- If the baseline does not fail with exactly two failures, confirm you have not already fixed one of the timeout example files.
- If `429` still does not appear after Task A, confirm you added both `"transient": true` and `"delay-in-seconds": 2`, and that `times:2` is still present for the `other` query.
- If `202` still does not appear after Task B, confirm you added both `"transient": true` and `"delay-in-seconds": 2`, and that the request body still uses `UniqueName`, `book`, and `9`.
- If Task C still fails for `202`, confirm `type` and `inventory` are using the `$match(dataType:..., value:each, times:1)` form instead of fixed values.
- If Docker reports port conflicts, stop the conflicting services and rerun the same command.

## Pass criteria
- Baseline run fails with exactly two failing scenarios: one `429`, one `202`.
- After Task A, only the `202` scenario remains failing.
- After Task B, the base resiliency flow passes with `schemaResiliencyTests: none`.
- After Task C, the full suite passes with `schemaResiliencyTests: all`.

## What you learned
- `429` is a contract-level resilience behavior, not just an implementation detail.
- `202 Accepted` is useful when work is deferred because a downstream dependency is slow.
- Specmatic examples can model downstream latency and verify both graceful degradation and recovery without changing application code.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
