# Studio Lab: Response Templating via Direct substitution and Data lookup

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

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/test/*.json` - External examples for the BFF API tests.
- `examples/mock/*.json` - External examples for mock.
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
Tests run: 4, Successes: 1, Failures: 3, Errors: 0
```

### 2. Loop Test using CLI
```shell
docker compose up
```
This will start the mock server and run the tests against it. You should see the same results in the terminal output as you did in Studio:

```terminaloutput
Tests run: 4, Successes: 1, Failures: 3, Errors: 0
```

## Goal of this lab
The goal of this lab is to use direct substitution and data lookup to fix the failed tests.

### Final Output
After implementing direct substitution and data lookup, you should see the following output when you run the tests

```terminaloutput
Tests run: 4, Successes: 4, Failures: 0, Errors: 0
```