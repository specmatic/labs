<!---
reports:
  ctrf: false
  html: false
--->

# Studio Lab: Partial Examples

## Objective
Use Specmatic Studio to repair incomplete external examples with partial examples, then verify the examples validate successfully.

## Why this lab matters
Some APIs may have a lot of transient, but mandatory fields which does not matter for your use-case. In such cases, instead of putting random values for such fields, partial examples let you keep only the fields that matter, without having to fill every field. Specmatic will fill in the missing fields for you to ensure the request/response is valid.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/partial-examples`.
- Ports `9000` and `9001` are available for Studio.

## Files in this lab
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`: OpenAPI contract for the BFF API, loaded by `specmatic.yaml`.
- `examples/*.json`: Incomplete external examples that will be fixed using partial examples.
- `specmatic.yaml`: Specmatic configuration for contract testing and mocking.
- `docker-compose.yaml`: Suite loop setup.

## Lab Rules
- Do not edit the shared contract in `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`.
- Edit only files under `examples/`.
- When fixing the two create examples, use partial examples instead of clicking Studio's automatic `Fix` button.

## Specmatic references
- Partial examples: [https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples](https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples)
- Specmatic Studio: [https://docs.specmatic.io/getting_started/studio_quick_start.html](https://docs.specmatic.io/getting_started/studio_quick_start.html)

## Lab Implementation Phases

### Baseline Phase

Validate the original incomplete examples and observe the intentional failures.

Test Run Cmd (Linux/Mac OSX)

```shell
docker run --rm \
  -v "${PWD}:/usr/src/app" \
  -v "${PWD}/../license.txt:/specmatic/specmatic-license.txt:ro" \
  specmatic/enterprise:latest \
  validate
```

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[FAIL] Examples: 0 passed and 3 failed out of 3 total
```

Windows PowerShell single-line

```powershell
docker run --rm -v "$($PWD.Path):/usr/src/app" -v "$((Resolve-Path ..\license.txt).Path):/specmatic/specmatic-license.txt:ro" specmatic/enterprise:latest validate
```

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[FAIL] Examples: 0 passed and 3 failed out of 3 total
```

### Studio Phase

Start Studio:

```shell
docker compose --profile studio up studio
```

#### Learner task: fix 3 examples using partial examples
In Studio, open `product_search_bff_v6.yaml` which should be under `.specmatic/repos/labs-contracts/common/openapi/order-bff` from the left sidebar. You will see that 3 examples have failed validation on the `examples` tab.

**Please do not click the `Fix` button to make these examples valid. Instead, use [partial examples](https://docs.specmatic.io/contract_driven_development/service_virtualization#partial-examples) to fix them.**

Fix the examples using partial examples:
- Convert `examples/test_accepted_order_request.json` into a partial example for the create-order flow.
- Convert `examples/test_accepted_product_request.json` into a partial example for the create-product flow.
- Update `examples/test_find_available_products_book_200.json` so it uses the contract-compliant query and date shape.

Expected output:

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[OK] Examples: 3 passed and 0 failed out of 3 total
```

Stop Studio after the examples are saved:

```shell
docker compose --profile studio down -v
```

Alternatively, just run the following command:

```shell
docker run --rm --entrypoint sh -v "${PWD}:/usr/src/app" specmatic/enterprise:latest -lc '
sed -i "2i\\  \\\"partial\\\": {" examples/test_accepted_order_request.json &&
sed -i "\$i\\  }" examples/test_accepted_order_request.json &&
sed -i "2i\\  \\\"partial\\\": {" examples/test_accepted_product_request.json &&
sed -i "\$i\\  }" examples/test_accepted_product_request.json &&
sed -i "s#\\\"path\\\": \\\"/findAvailableProducts\\\"#\\\"path\\\": \\\"/findAvailableProducts?type=book\\\"#" examples/test_find_available_products_book_200.json &&
sed -i "/\\\"query\\\": {/a\\            \\\"from-date\\\": \\\"2025-10-01\\\",\\n            \\\"to-date\\\": \\\"2025-10-15\\\"" examples/test_find_available_products_book_200.json &&
sed -i "/\\\"type\\\": \\\"book\\\"/d" examples/test_find_available_products_book_200.json
'
```

### Final Phase

Re-run validation with the Windows PowerShell command after the Studio fixes are saved.

Windows PowerShell single-line

```powershell
docker run --rm -v "$($PWD.Path):/usr/src/app" -v "$((Resolve-Path ..\license.txt).Path):/specmatic/specmatic-license.txt:ro" specmatic/enterprise:latest validate
```

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[OK] Examples: 3 passed and 0 failed out of 3 total
```

## Loop Test

### Loop Test in Studio
In Studio, after examples are valid:

- Go to `Mock` and click `Run` (mock server on port `8080`).
- Go to `Test`, set URL to `http://127.0.0.1:8080`, then click `Run`.

Expected: `7` tests passing and `0` failing.

### Stop Studio

```shell
docker compose --profile studio down -v
```

### Why 7 tests?
You have 3 external examples, plus additional inline examples in the OpenAPI spec.  
Specmatic runs tests from both sources, so total generated tests are higher than 3.

### Loop Test using CLI

Run the following command to start the mock server and run the tests against it using CLI.

```shell
docker compose up --abort-on-container-exit
```

This runs the suite, starts the dependency mocks, and executes the tests. You should see:

```terminaloutput
Tests run: 7, Successes: 6, Failures: 0, WIP: 1, Errors: 0
```

```shell
docker compose down -v
```

## Pass Criteria
- Validation shows: `3 passed and 0 failed out of 3 total`.
- Loop test shows: `Tests run: 7, Successes: 6, Failures: 0, WIP: 1, Errors: 0`.


## What you learned
- Partial examples let you keep only the contract-relevant fields in an example.
- Studio can help you diagnose incomplete examples and save the corrected files quickly.
- External examples and inline examples can both contribute to the final loop test count.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
