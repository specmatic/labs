# Studio Lab: Schema Resiliency Testing

This lab demonstrates how to use Specmatic's schema resiliency testing features to ensure your API operates as expected by HTTP standards. 
Here we'll send contract-invalid requests and ensure the API handles it gracefully.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec, and it's example files.

## Start Studio using Docker
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

## Loop Test

### 1. Loop Test in Studio
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples are valid.

Go to the Mock tab and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, set url as `http://localhost:8080` and click on the "Run" button to run the tests against the mock server.

You should see 

```terminaloutput
Tests run: 6, Successes: 6, Failures: 0, Errors: 0
```

### 2. Loop Test using CLI
```shell
docker compose up
```
This will start the mock server and run the tests against it. You should see the same results in the terminal output as you did in Studio:

```terminaloutput
Tests run: 6, Successes: 6, Failures: 0, Errors: 0
```

## Goal of this lab
The goal of this lab is to try different schema resiliency testing levels and see how the number of tests vary and how the coverage changes.

### Positive Only Tests
By setting the level to `positiveOnly` you should see

```terminaloutput
Tests run: 42, Successes: 42, Failures: 0, Errors: 0
```

### Positive and Negative Tests (ALL)
By setting the level to `all` you should see

```terminaloutput
Tests run: 596, Successes: 596, Failures: 0, Errors: 0
```

### Computation - How did Specmatic generate 148 tests?

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