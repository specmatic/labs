# Sample Contract Testing and API Mocking Demo

## Background
In this sample project, we will use [Specmatic](https://specmatic.io) to contract test the BFF (Backend for Frontend) in isolation. 
BFF is dependent on Domain API and Kafka. Using this sample project we'll demonstrate both OpenAPI and AsyncAPI support in Specmatic.

Following are the specifications used in this project:

* `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` is the shared BFF contract used for running contract tests against the BFF.
* `.specmatic/repos/labs-contracts/common/openapi/order-api/api_order_v5.yaml` is the shared Domain API contract used for stubbing the Domain API.
* `.specmatic/repos/labs-contracts/common/asyncapi/product-audits/kafka.yaml` defines the shared topics and message schema used for mocking Kafka interactions.

### Application Architecture
![HTML client talks to BFF API, which in turn talks to backend API](assets/application-architcture.gif)

### Contract Testing Setup
![Contract testing setup with Specmatic](assets/specmatic-contract-test-setup.gif)

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/order-bff`.

## Run Contract Tests

### 1. Using Specmatic Studio (Recommended for Local Development)

```shell
docker compose --profile studio up
```
This will start the Specmatic Studio and the System Under Test (SUT) [BFF in this case] in Docker containers. 
Once the containers are up and running, open [Specmatic Studio](http://localhost:9000/_specmatic/studio) in your browser. 
In Studio, on the left sidebar, open `specmatic.yaml` and click on `Run Suite` to start all dependencies as mocks and execute the contract tests against the SUT. The suite checks out its contracts under `.specmatic/repos/labs-contracts`, and you can inspect those files from the left sidebar if needed.

When the tests complete, you should see the following in the status header indicating that the contract tests run successfully:

![Test results in Specmatic Studio](assets/studio-bff-test-results.png)

```shell
docker compose --profile studio down -v
```

### 2. Using Docker (Recommended for CI)
```shell
docker compose --profile test up --abort-on-container-exit
```

In the logs, you should see the following lines indicating that the contract tests run successfully:

```terminaloutput
Tests run: 227, Successes: 223, Failures: 0, Errors: 4
```

```shell
docker compose --profile test down -v
```

Also look at the [detailed contract report](build/reports/specmatic/test/html/index.html) to see the details of the tests that were run.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
