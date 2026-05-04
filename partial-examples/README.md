---
lab_schema: v2
reports:
  ctrf: false
  html: false
---
# Studio Lab: Partial Examples

## Objective
Use Specmatic Studio to repair incomplete external examples with partial examples, then verify the examples validate successfully.

## Why this lab matters
Teams often start with incomplete examples while they are still exploring a workflow. Partial examples let you keep only the fields that matter for the contract behavior you want to document, without having to fill every generated field exactly.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/partial-examples`.
- Ports `9000` and `9001` are available for Studio.

## Architecture
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` is the shared OpenAPI contract loaded through `specmatic.yaml`.
- `docker run ... validate` checks the external examples from the CLI.
- `docker compose --profile studio up studio` starts Studio so you can inspect and fix the incomplete examples interactively.
- `docker compose up --abort-on-container-exit` runs the loop test suite against the mock setup.

## Files in this lab
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` - OpenAPI contract for the BFF API, loaded by `specmatic.yaml`.
- `examples/test_accepted_order_request.json` - incomplete external example that should become a partial example.
- `examples/test_accepted_product_request.json` - incomplete external example that should become a partial example.
- `examples/test_find_available_products_book_200.json` - search example you will make contract-compliant.
- `specmatic.yaml` - Specmatic configuration for contract testing and mocking.
- `docker-compose.yaml` - loop test setup.

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
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[FAIL] Examples: 0 passed and 3 failed out of 3 total
```

Windows (PowerShell/CMD) single-line

```shell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
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

In Studio, open `product_search_bff_v6.yaml` from `.specmatic/repos/labs-contracts/common/openapi/order-bff` in the left sidebar. You should see three failed examples on the **Examples** tab.

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

### Final Phase

Re-run validation with the Windows single-line command after the Studio fixes are saved.

Windows (PowerShell/CMD) single-line

```shell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
```

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[OK] Examples: 3 passed and 0 failed out of 3 total
```

Optional loop test using CLI:

```shell
docker compose up --abort-on-container-exit
```

```terminaloutput
Tests run: 7, Successes: 7, Failures: 0, Errors: 0
```

```shell
docker compose down -v
```

## Pass Criteria
- Validation shows `3 passed and 0 failed out of 3 total` after the fixes.
- If you run the optional loop test, it shows `Tests run: 7, Successes: 7, Failures: 0, Errors: 0`.

## Troubleshooting
- If Studio does not start, confirm that ports `9000` and `9001` are free.
- If validation still shows the original failures, confirm that the updated files were saved under `examples/`.
- If the loop test count is higher than `3`, remember that Specmatic is using both external examples and additional inline examples from the OpenAPI spec.

## Cleanup
- The Studio phase already ends with `docker compose --profile studio down -v`.
- If you ran the optional loop test, it already ends with `docker compose down -v`, so no additional cleanup is required.

## What you learned
- Partial examples let you keep only the contract-relevant fields in an example.
- Studio can help you diagnose incomplete examples and save the corrected files quickly.
- External examples and inline examples can both contribute to the final loop test count.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
