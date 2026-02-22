# Studio Lab: Partial Examples

## Objective
Use Specmatic Studio to repair incomplete external examples using partial examples, then verify behavior using validation and loop testing.

## Prerequisites
- Docker is installed and running.
- You are in `labs/partial-examples`.

## Time
10 minutes.

## Files in this lab
- `specs/simple-openapi-spec.yaml`: OpenAPI contract for the BFF API.
- `examples/*.json`: Incomplete external examples that will be fixed using partial examples.
- `specmatic.yaml`: Specmatic configuration for contract testing and mocking.
- `docker-compose.yaml`: Mock + test loop setup.

## Validate the examples (intentional failure)
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

## Start Studio
```shell
docker run --rm \
  --name studio \
  --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```

Open [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) in Studio. You will see 3 failing external examples.

## Learner task: fix 3 examples using partial examples
Please do not click the `Fix` button to make these examples valid. Instead, use [partial examples](https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples) to fix them.

## Re-validate after fixing in Studio
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

## Reference
- Partial examples docs: [https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples](https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples)

## Loop Test

### Loop Test in Studio
In Studio, after examples are valid:

- Go to `Mock` and click `Run` (mock server on port `8080`).
- Go to `Test`, set URL to `http://127.0.0.1:8080`, then click `Run`.

Expected: `7` tests passing and `0` failing.

### Why 7 tests?
You have 3 external examples, plus additional inline examples in the OpenAPI spec.  
Specmatic runs tests from both sources, so total generated tests are higher than 3.

### Loop Test using CLI

Stop Studio and run the following command to start the mock server and run the tests against it using CLI.

```shell
docker compose up
```
This starts the mock server and runs the tests against it. You should see:

```terminaloutput
Tests run: 7, Successes: 7, Failures: 0, Errors: 0
```

```shell
docker compose down
```

## Pass Criteria
- Validation shows: `3 passed and 0 failed out of 3 total`.
- Loop test shows: `Tests run: 7, Successes: 7, Failures: 0, Errors: 0`.
