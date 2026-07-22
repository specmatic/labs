# Testing Event Flows and Behaviors

Testing event-driven systems is fundamentally harder than testing REST APIs. Validating schemas is straightforward, but validating behavior in terms of what the system actually does when it receives or produces an event is still a major challenge. Teams often struggle to trigger their systems reliably, observe side effects, and automate end-to-end event flow testing without custom scripts or brittle harnesses.

This sample project demonstrates how to validate an event flow in a Kafka-based system using Specmatic Enterprise. It includes a simple Spring Boot application that listens to messages on a Kafka topic, processes them, and then publishes a reply message to another topic. It also handles notification and update events. The contract tests validate the behavior of these event flows using Specmatic's contract testing capabilities.

Here we are using [AsyncAPI 3.0.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.0.0).

## Background

This project includes a consumer (`OrderService`) that implements the following behavior:
* listens to messages on `new-order` topic and then upon receiving a message, it processes the same and publishes a reply message to `wip-order` topic. Thereby it demonstrates the [request reply pattern](https://www.asyncapi.com/docs/tutorials/getting-started/request-reply) in AsyncAPI 3.0.0 specification.
* on receiving an update (via RESTful API call) from the `WarehouseService`, the `OrderService` updates the order status to `accepted` and publishes a message on `accepted-orders` topic. Thereby it demonstrates the event notification pattern.
* on receiving a message on the `out-for-delivery-orders` topic from the `Shipping App`, the `OrderService` updates the order status to `shipped` and triggers the `TaxService` to generate a tax invoice. Thereby it demonstrates the fire-and-forget pattern.

![Order Application Workflow](assets/order-application-workflow.gif)

## Time required to complete this lab
10-15 minutes.

## Objective
Use ready-made examples to prove async example substitution and capture work across:
- `before` fixtures
- `send` messages
- `receive` messages
- `after` fixtures

## Prerequisites
- Docker is installed and running.
- You are in `labs/async-event-flow`.

## What this lab now demonstrates

### 1. `acceptOrder.json`: example data lookup -> `before` fixture capture -> later `before` fixture substitution -> `send` substitution

Flow:
1. Example `data.dataLookups.acceptance` provides order id, invoice date, and timestamp.
2. First `before` fixture calls TaxService mock using `$(dataLookups.acceptance[ORDER_ID].orderId)` and `$(dataLookups.acceptance[ORDER_ID].invoiceDate)`.
3. Fixture captures `ORDER_ID` and `INVOICE_ID` from mock response.
4. Second `before` fixture uses captured `$(ORDER_ID)` and data lookup timestamp in `PUT /orders`.
5. Async `send` expectation uses captured `$(ORDER_ID)` and the same data lookup timestamp.

This proves:
- example data lookup works in fixtures and async messages
- fixture request substitution works
- fixture response capture works
- captured values flow into async `send`

### 2. `outForDeliveryOrder.json`: example data lookup -> `before` fixture capture -> `receive` substitution -> `after` capture -> later `after` substitution

Flow:
1. Example `data.dataLookups.delivery` provides order id, delivery address, delivery date, and TaxService expectation id.
2. `before` fixture uses `$(dataLookups.delivery[ORDER_ID].orderId)` to fetch existing shipped order and captures `ORDER_ID`.
3. `receive` payload uses captured `$(ORDER_ID)` plus delivery data lookups.
4. App processes message, updates order, calls TaxService mock.
5. First `after` fixture fetches stored order, captures `ORDER_ID`, `DELIVERY_DATE`, `ORDER_STATUS`.
6. Second `after` fixture verifies downstream call using `$(dataLookups.delivery[ORDER_ID].taxInvoiceExampleId)`.

This proves:
- example data lookup works before capture and after capture
- async `receive` substitution works
- `after` fixture capture works
- captured values flow into later `after` fixtures

## How to test these event flows

Specmatic solves event-flow testing by combining:
1. **Contract validation** from `.specmatic/repos/labs-contracts/asyncapi/async-event-flow/async-order-service.yaml` (topics, payload schemas, headers, request-reply mappings).
2. **Scenario examples** from `examples/async-order-service/*.json` that describe concrete interactions and expected behavior.

In this sample, each example acts like an executable test case:
- `receive`: the input event Specmatic publishes to Kafka (for consumer flows).
- `send`: the output event Specmatic expects your app to publish.
- `before`: a setup fixture that runs before assertion of the scenario.
- `after`: a verification fixture that runs after the event flow is triggered, used to assert side effects.

Examples now pass as-is. Error drills below let you force failures and inspect report output.

### How contract tests validate behavior (not just shape)

For request-reply style flows (for example `newOrder.json`), Specmatic:
1. sends a `receive` event on `new-orders`,
2. waits for your service to process it,
3. verifies a corresponding `send` event appears on `wip-orders` with matching payload and headers.

This ensures the event contract is honored end-to-end, including correlation headers and transformed payload values.

### `before` fixture (arrange/setup)

`before` is setup fixture. In `acceptOrder.json`, first `before` fixture uses example data lookup and captures `ORDER_ID` from mock response, next `before` fixture uses captured value in `PUT /orders`, then Specmatic validates async `send` message using same captured value. In `outForDeliveryOrder.json`, `before` fixture uses example data lookup to fetch the seeded order, captures `ORDER_ID`, then `receive` uses it.

Use `before` when your event is produced as a side effect of some trigger (REST call, seed action, prerequisite state).

### `after` fixture (assert side effects)

`after` is verification fixture. In `outForDeliveryOrder.json`, first `after` fixture captures persisted response fields, second `after` fixture verifies downstream TaxService mock call.

Use `after` when correctness depends on side effects beyond one output topic (DB state, downstream HTTP calls, idempotency outcomes).

Together, `receive`/`send` plus `before`/`after` fixtures let you express full event behavior as contract-driven scenarios, without writing custom test harness code.

![Event flow Verification](assets/async-interaction-validation.gif)

## Run contract tests
1. Start Kafka, the sample service, and Specmatic Studio.
```shell
docker compose up -d
```
   
2. Go to [Studio](http://127.0.0.1:9000/_specmatic/studio) and open the [specmatic.yaml](specmatic.yaml) file from the left sidebar, click on "Run Suite", and use the checked-out contract under `.specmatic/repos/labs-contracts/asyncapi/async-event-flow/async-order-service.yaml` if you want to inspect the loaded AsyncAPI file in Studio.

If your local image tag differs from `specmaticdemo/specmatic-kafka-sample-asyncapi3`, update `sut.image` in `docker-compose.yaml` before run.

Run suite:

```shell
docker compose exec -T studio specmatic run-suite
```

```terminaloutput
Tests run: 4, Successes: 4, Failures: 0, WIP: 0, Errors: 0
```

## Files to inspect

- `examples/async-order-service/acceptOrder.json`
- `examples/async-order-service/outForDeliveryOrder.json`
- `examples/tax-service/raise-invoice-order-123.json`

Search for:
- `$(ORDER_ID)`
- `$(dataLookups.acceptance[ORDER_ID].orderId)`
- `$(dataLookups.delivery[ORDER_ID].deliveryDate)`
- `(ORDER_ID:number)`

Specmatic data lookup syntax is:

```text
$(dataLookups.<dictionary>[<CAPTURED_VARIABLE>].<key>)
```

If `<CAPTURED_VARIABLE>` is not available yet, Specmatic uses the `*` entry in the dictionary. This lets a first `before` fixture use example data before any fixture has captured values.

## Error drills

Use these one by one. Re-run `docker compose exec -T studio specmatic run-suite` after each edit.

### 1. Break `before` fixture substitution

In `acceptOrder.json`, change:

```json
"orderId": "$(dataLookups.acceptance[ORDER_ID].orderId)"
```

to:

```json
"orderId": "$(dataLookups.acceptance[ORDER_ID].missingOrderId)"
```

Expected:
- `ACCEPT_ORDER` fails before async assertion
- CTRF/HTML should show `before` fixture error with data lookup failure context

### 2. Break async `send` substitution

In `acceptOrder.json`, change:

```json
"timestamp": "$(dataLookups.acceptance[ORDER_ID].timestamp)"
```

to:

```json
"timestamp": "$(dataLookups.acceptance[ORDER_ID].missingTimestamp)"
```

Expected:
- async scenario fails while building outgoing expected message
- report should surface message substitution error

### 3. Break async `receive` substitution

In `outForDeliveryOrder.json`, change:

```json
"deliveryDate": "$(dataLookups.delivery[ORDER_ID].deliveryDate)"
```

to:

```json
"deliveryDate": "$(dataLookups.delivery[ORDER_ID].missingDeliveryDate)"
```

Expected:
- `ORDER_OUT_FOR_DELIVERY` fails before publish
- report should show receive payload substitution failure

### 4. Break `after` fixture substitution

In `outForDeliveryOrder.json`, change:

```json
"/_specmatic/verify?exampleIds=$(dataLookups.delivery[ORDER_ID].taxInvoiceExampleId)"
```

to:

```json
"/_specmatic/verify?exampleIds=$(dataLookups.delivery[ORDER_ID].missingTaxInvoiceExampleId)"
```

Expected:
- first `after` fixture passes
- second `after` fixture fails with substitution error
- CTRF/HTML should show `after` fixture failure details

### 5. Break `after` verification count

In `outForDeliveryOrder.json`, change:

```json
"tax-invoice-for-order-456": "$match(exact: 1)"
```

to:

```json
"tax-invoice-for-order-456": "$match(exact: 2)"
```

Expected:
- second `after` fixture runs
- failure bubbles into report as post-condition failure

### Reset

Revert examples to checked-in versions, then rerun suite.

### Cleanup

Bring down the Kafka broker after the tests are done.

```shell
docker compose down -v
```

## Troubleshooting

If the suite does not start, retry after pulling the latest images:
```shell
docker compose pull
```

If `specmatic run-suite` fails with:

```text
Error executing git rev-parse --abbrev-ref HEAD
fatal: not a git repository
```

then local `.specmatic` checkout is stale/partial. Delete `./.specmatic/repos/labs-contracts` and rerun so Specmatic can recreate checkout.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
