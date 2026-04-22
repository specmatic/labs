# Studio Lab: Schema Resiliency Testing

This lab demonstrates how to use Specmatic's schema resiliency testing features to ensure your API operates as expected by HTTP standards. 
Here we'll send contract-invalid requests and ensure the API handles it gracefully.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/schema-resiliency-testing`.

## Files in this lab
- `.specmatic/repos/labs-contracts/openapi/schema-resiliency/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API, loaded by `specmatic.yaml`. This is the main contract used in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec, and it's example files.

## Start Studio using Docker Compose
```shell
docker compose --profile studio up studio
```

## Loop Test

### 1. Loop Test in Studio
In Studio, open `specmatic.yaml` from the left sidebar. The suite loads the contract into `.specmatic/repos/labs-contracts/openapi/schema-resiliency/simple-openapi-spec.yaml`, and you will see that 3 examples are valid. Open that checked-out file from the left sidebar if you want to inspect it directly.

Go to the Mock tab and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, set url as `http://localhost:8080` and click on the "Run" button to run the tests against the mock server.

You should see 

```terminaloutput
Tests run: 3, Successes: 3, Failures: 0, Errors: 0
```

Stop Studio before moving to the next steps:
```shell
docker compose --profile studio down -v
```

### 2. Loop Test using CLI

Start docker containers

```shell
docker compose up --abort-on-container-exit
```
This will run the suite, start the dependency mock, and run the tests against it. You should see the same results in the terminal output as you did in Studio:

Expected console output:

```terminaloutput
Tests run: 3, Successes: 3, Failures: 0, Errors: 0
```

Clean up
```shell
docker compose down -v
```

## Goal of this lab
The goal of this lab is to try different schema resiliency testing levels and see how the number of tests varies and how coverage changes.

### Positive Only Tests
In `specmatic.yaml` change `schemaResiliencyTests: none` to `schemaResiliencyTests: positiveOnly`

#### Run Positive only Tests

Start docker containers

```shell
docker compose up --abort-on-container-exit
```

Expected console output:

```terminaloutput
Tests run: 42, Successes: 42, Failures: 0, Errors: 0
```

Clean up
```shell
docker compose down -v
```

### Positive and Negative Tests (ALL)
In `specmatic.yaml` change `schemaResiliencyTests: positiveOnly` to `schemaResiliencyTests: all`

#### Run all Tests

Start docker containers

```shell
docker compose up --abort-on-container-exit
```

Expected console output:

```terminaloutput
Tests run: 600, Successes: 600, Failures: 0
```

Clean up
```shell
docker compose down -v
```

### Out of License Limit
You might see issues because of the license limit of 600 tests. With non-trail enterprise license, you won't face this issue. However, this brings up an interesting topic: how do I can control or reduce the number of generated tests?

Check out the documentation on [maxTestRequestCombinations](https://docs.specmatic.io/contract_driven_development/contract_testing#limiting-the-count-of-tests)

### Computation - How did Specmatic generate so many tests?

| Fields    | Data Types | Required | Nullable | Constraints | Values                    |
|-----------|------------|----------|----------|-------------|---------------------------|
| name      | string     | Yes      | No       |             |                           |
| type      | string     | Yes      | No       | Enum        | book, food, gadget, other |
| inventory | number     | Yes      | No       | min & max   | min = 1, max = 9999       |
| cost      | number     | No       | Yes      | min         | min = 0.01                |

| Positive Variations                 | Negative Variations             | Variation Count |
|-------------------------------------|---------------------------------|-----------------|
| string                              | number, boolean, null           | 4               |
| 4 enum value                        | non-enum, number, boolean, null | 8               |
| 1, (1 < random number < 9999), 9999 | 0, 10000, string, boolean, null | 8               |
| 0.01, random number, null           | 0.00, string, boolean           | 6               |

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
