---
lab_schema: v2
reports:
  ctrf: false
  html: false
  readme_summary: true
  console_summary: true
---
# Studio Lab: Validate, Fix, and Generate External Examples

## Objective
Use Specmatic Studio and `validate` to reproduce failing external examples, fix invalid examples, add missing `201` examples for create APIs, and re-run validation to a clean pass.

## Why this lab matters
Teams often keep executable examples outside the OpenAPI file so domain teams can update test cases without editing the contract itself. This lab shows how Specmatic validates those external examples and catches drift early.

## Time required
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/external-examples`.
- Ports `9000` and `9001` are free for Studio.

## Architecture
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` is the shared OpenAPI contract loaded through `specmatic.yaml`.
- `examples/*.json` contains external examples that Specmatic validates against that contract.
- `docker run ... validate` checks the examples from the CLI.
- `docker compose --profile studio up` starts Studio so you can inspect, fix, and generate examples interactively.

## Files in this lab
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` - shared OpenAPI contract for the BFF API, loaded by `specmatic.yaml` after checkout.
- `examples/*.json` - external examples validated against the contract.
- `specmatic.yaml` - Specmatic config that points to the contract and the examples directory.

## Lab Rules
- Do not edit the shared contract in `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`.
- Edit only files under `examples/`.

## Specmatic references
- External examples: [https://docs.specmatic.io/features/external_examples](https://docs.specmatic.io/features/external_examples)
- Specmatic Studio: [https://docs.specmatic.io/getting_started/studio_quick_start.html](https://docs.specmatic.io/getting_started/studio_quick_start.html)
- Overview video: [Watch the external examples overview](https://www.youtube.com/watch?v=TcNayIEP4sw)

## Lab Implementation Phases

### Baseline Phase
<!--
phase-meta
id: baseline
kind: baseline
validates_test_counts: true
expected_reports:
  readme_summary: true
  console_summary: true
  ctrf: false
  html: false
os_scope: all
-->
Bring the current examples to a fully valid state and ensure all required create-scenario examples are present.

Run:

```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

Expected output:

```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[FAIL] Examples: 1 passed and 3 failed out of 4 total
```

Windows (PowerShell or CMD):

```powershell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
```

Expected output:

```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[FAIL] Examples: 1 passed and 3 failed out of 4 total
```

### Studio Phase
<!--
phase-meta
id: studio-fix
kind: studio
validates_test_counts: false
expected_reports:
  readme_summary: false
  console_summary: false
  ctrf: false
  html: false
os_scope: all
-->
Start Studio:

```powershell
docker compose --profile studio up
```

Expected output:

```terminaloutput
Attaching to studio-1
```

In Studio, open `product_search_bff_v6.yaml` from `.specmatic/repos/labs-contracts/common/openapi/order-bff`. You should see three failed examples in the **Examples** tab.

Update the failing examples:
1. `examples/test_find_available_products_book_200.json`
   - Change `query.to-date` from `"today"` to a valid ISO date, for example `"2025-11-28"`.
2. `examples/test_accepted_product_request.json`
   - Change `body.type` from `"movie"` to one of `book`, `food`, `gadget`, or `other`.
   - Change `body.inventory` from `"five"` to a number, for example `5`.
3. `examples/test_accepted_order_request.json`
   - Add missing required property `count`, for example `2`, in the request body.

Still in Studio, generate examples for:
- `POST /products` with response `201`
- `POST /orders` with response `201`

Stop Studio after the fixes and generated examples are saved:

```powershell
docker compose --profile studio down -v
```

Expected output:

```terminaloutput
Container external-examples-studio-1  Removed
Network external-examples_default  Removed
```

### Final Phase
<!--
phase-meta
id: final
kind: final
validates_test_counts: true
expected_reports:
  readme_summary: true
  console_summary: true
  ctrf: false
  html: false
os_scope: all
-->
Re-run validation:

```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

Expected output:

```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[OK] Examples: 6 passed and 0 failed out of 6 total
```

Windows (PowerShell or CMD):

```powershell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
```

Expected output:

```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[OK] Examples: 6 passed and 0 failed out of 6 total
```

## Pass Criteria
- Baseline validation reports `1 passed and 3 failed out of 4 total`.
- After the Studio fixes and generated examples, validation reports `6 passed and 0 failed out of 6 total`.
- Overall validation result is `PASSED`.

## Troubleshooting
- If Studio does not start, confirm that ports `9000` and `9001` are free.
- If validation still reports the old failing examples, confirm that the saved files are under `examples/` and that the generated `201` examples were written there.

## Cleanup
The Studio phase already shuts the Studio stack down. After the final phase, no additional cleanup is required.

## What you learned
- External examples can live outside the OpenAPI document while still being validated against the contract.
- Studio can help diagnose and fix invalid examples quickly.
- Generated examples are a practical way to fill missing create-scenario coverage without editing the contract.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
