# Testing Event Flows and Behaviors

Testing event-driven systems is fundamentally harder than testing REST APIs. Validating schemas is straightforward, but validating behavior in terms of what the system actually does when it receives or produces an event is still a major challenge. Teams often struggle to trigger their systems reliably, observe side effects, and automate end-to-end event flow testing without custom scripts or brittle harnesses.

This sample project demonstrates how we can run validate an event flow in a Kafka-based system using Specmatic enterprise. It includes a simple Spring Boot application that listens to messages on a Kafka topic, processes them, and then publishes a reply message to another topic. It also handles notification and update events. The contract tests validate the behavior of these event flow using Specmatic's contract testing capabilities.

Here we are using [AsyncAPI 3.0.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.0.0).

## Background

This project includes a consumer (`OrderService`) which implements following behaviour:
* listens to messages on `new-order` topic and then upon receiving a message, it processes the same and publishes a reply message to `wip-order` topic. Thereby it demonstrates the [request reply pattern](https://www.asyncapi.com/docs/tutorials/getting-started/request-reply) in AsyncAPI 3.0.0 specification.
* on receiving an update (via RESTful API call) from the `WarehouseService`, the `OrderService` updates the order status to `accepted` and publishes a message on `accepted-orders` topic. Thereby it demonstrates the event notification pattern.
* on receiving a message on the `out-for-delivery-orders` topic from the `Shipping App`, the `OrderService` updates the order status to `shipped` and triggers the `TaxService` to generate a tax invoice. Thereby it demonstrates the fire-and-forget pattern.

![Order Appplication Workflow](assets/order-application-workflow.gif)

## How to Test these event flows?

Specmatic solves event-flow testing by combining:
1. **Contract validation** from `specs/async-order-service.yaml` (topics, payload schemas, headers, request-reply mappings).
2. **Scenario examples** from `examples/async-order-service/*.json` that describe concrete interactions and expected behavior.

In this sample, each example acts like an executable test case:
- `receive`: the input event Specmatic publishes to Kafka (for consumer flows).
- `send`: the output event Specmatic expects your app to publish.
- `before`: setup actions that run before assertion of the scenario.
- `after`: verification actions that run after the event flow is triggered, used to assert side effects.

### How contract tests validate behavior (not just shape)

For request-reply style flows (for example `newOrder.json`), Specmatic:
1. sends a `receive` event on `new-orders`,
2. waits for your service to process it,
3. verifies a corresponding `send` event appears on `wip-orders` with matching payload and headers.

This ensures the event contract is honored end-to-end, including correlation headers and transformed payload values.

### `before` syntax (arrange/setup)

`before` is used to establish preconditions. In `acceptOrder.json`, `before` triggers an HTTP `PUT /orders` so the app performs the action that should publish the `accepted-orders` event. Specmatic then validates that app correctly published the `send` event on the expected topic as per the asyncapi spec.

Use `before` when your event is produced as a side effect of some trigger (REST call, seed action, prerequisite state).

### `after` syntax (assert side effects)

`after` is used for post-conditions. In `outForDeliveryOrder.json`, after publishing the correct event on the Kafka topic, Specmatic:
- checks `GET /orders/456?status=SHIPPED` returns the updated stored status of the order, and
- checks the TaxService mock verification endpoint to confirm the invoice call happened (`exampleId=tax-invoice-for-order-456`).

Use `after` when correctness depends on side effects beyond one output topic (DB state, downstream HTTP calls, idempotency outcomes).

Together, `receive`/`send` plus `before`/`after` lets you express full event behavior as contract-driven scenarios, without writing custom test harness code.

![Event flow Verification](assets/async-interaction-validation.gif)

## Pre-requisites
* Gradle
* JDK 17+

## Run the tests

### 1. Using Specmatic-JUnit Helper

```shell
./gradlew test --tests="com.example.order.ContractTest"
```

### 2. Using TestContainers

```shell
./gradlew test --tests="com.example.order.ContractTestUsingTestContainer"
```

You will now see a detailed HTML report in `build/reports/index.html` with the messages that were sent and received as part of the contract tests.

## Run the contract tests using Specmatic Studio
1. Build the application using Gradle
```shell
./gradlew bootJar
```
2. Start the Kafka, Service and Studio.
```shell
docker compose up
```
   
3. Open the [specmatic.yaml](specmatic.yaml) file from the left sidebar, and click on the "Run Suite" button to run the tests against the service.

You should see 

```terminaloutput
Tests run: 6, Successes: 6, Failures: 0, Errors: 0
```

4. Bring down the Kafka broker after the tests are done.
```shell
docker compose down
```
