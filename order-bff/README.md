# Sample Contract Testing and API Mocking Demo

## Background
In this sample project, we will use [Specmatic](https://specmatic.io) to contract test the BFF (Backend for Frontend) in isolation. BFF is dependent on Domain API and Kafka. Using this sample project we'll demonstrate both OpenAPI and AsyncAPI support in Specmatic.

Following are the specifications used in this project:

* [BFF's OpenAPI spec](https://github.com/specmatic/specmatic-order-contracts/blob/main/io/specmatic/examples/store/openapi/product_search_bff_v4.yaml) is used for running contract tests against the BFF.
* [Domain API's OpenAPI spec](https://github.com/specmatic/specmatic-order-contracts/blob/main/io/specmatic/examples/store/openapi/api_order_v3.yaml) is used for stubbing the Domain API.
* [AsyncAPI spec](https://github.com/specmatic/specmatic-order-contracts/blob/main/io/specmatic/examples/store/asyncapi/kafka.yaml) of Kafka that defines the topics and message schema and is used for mocking interactions with Kafka.

![HTML client talks to BFF API which in-turn talks to backend API](assets/specmatic-order-bff-architecture.gif)

## Run Contract Tests

```shell
docker compose -f docker-compose-test.yaml up
```

In the logs, you should see the following lines indicating that the contract tests run successfully:

**Tests run: 227, Successes: 223, Failures: 0, Errors: 4**

Also look at the report in `build/reports/specmatic/html/index.html` to see the details of the tests that were run.
