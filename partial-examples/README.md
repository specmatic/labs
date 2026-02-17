# Studio Lab: Partial Examples

This lab demonstrates how to work with partial examples for an OpenAPI spec.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec, and it's example files.

## Validate the Examples
```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

### Output
```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[FAIL] Examples: 0 passed and 3 failed out of 3 total
```

## Start Studio using Docker
```shell
docker run --rm \
  --name studio \
  --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```

In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples have failed validation.

Click on each failed example to see the validation errors. We'll use partial examples feature to fix the examples.

## Re-validate the Examples after fixing in Studio using Partial Examples
```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

### Output
```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[OK] Examples: 3 passed and 0 failed out of 3 total
```

## Loop Test

### Loop Test in Studio
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples are valid.

Go to the Mock tab and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, set url as `http://localhost:8080` and click on the "Run" button to run the tests against the mock server.

You should see 7 tests passing and 0 tests failing.

### Why 7 tests?
The OpenAPI spec has 3 examples then why are we getting 7 tests?

### Loop Test using CLI

Stop Studio and run the following command to start the mock server and run the tests against it using CLI.

```shell
docker compose up
```
This will start the mock server and run the tests against it. You should see 

```terminaloutput
Tests run: 7, Successes: 7, Failures: 0, Errors: 0
```

```shell
docker compose down
```