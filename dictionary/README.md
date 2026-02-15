# Studio Lab: Dictionary to Generate Domain-Aware Request/Response Payloads

This lab demonstrates how to use Specmatic's Dictionary feature to generate domain-aware request/response payloads for contract testing and service virtualization.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec and it's example files.

## Run loop test using Docker
```shell
docker compose up
```

### Output
```terminaloutput
Tests run: 3, Successes: 0, Failures: 3, Errors: 0
```

### Root cause of the failed tests
Tests expect a specific value in the response body, but the mock is generating random values as it does not have examples. We will use dictionary feature to ensure the mock only use specific values defined in the dictionary file to generate the response.

## Re-run loop test using Docker after fixing the examples using dictionary
```shell
docker compose up
```

### Output
```terminaloutput
Tests run: 3, Successes: 3, Failures: 0, Errors: 0
```