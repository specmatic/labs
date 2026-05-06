<!---
reports:
  ctrf: false
  html: false
--->

# Studio Lab: Validate, Fix, and Generate External Examples

## Objective
Use Specmatic Studio and `validate` to reproduce failing external examples, fix invalid examples, add missing `201` examples for create APIs, and re-run validation to a clean pass.

## Why this lab matters
Teams often keep executable examples outside the OpenAPI file so domain teams can update test cases without editing the contract itself. This lab shows how Specmatic validates those external examples and catches drift early.

### Overview Video

Watch the external video -[Watch the external examples overview](https://www.youtube.com/watch?v=TcNayIEP4sw)

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/external-examples`.
- Ports `9000` and `9001` are free for Studio.

## Architecture
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` is the shared OpenAPI contract loaded through `specmatic.yaml`.
- `docker run ... validate` checks the examples from the CLI.
- `docker compose --profile studio up` starts Studio so you can inspect, fix, and generate examples interactively.

## Files in this lab
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml` - shared OpenAPI contract for the BFF API, loaded by `specmatic.yaml` after checkout.
- `specmatic.yaml` - Specmatic config that points to the contract and the examples directory.
- book_200: `examples/test_find_available_products_book_200.json`
- accepted_product: `examples/test_accepted_product_request.json`
- accepted_order: `examples/test_accepted_order_request.json`
- too_many: `examples/test_products_too_many_requests.json`
- created_product: `examples/test_created_product_request_201.json`
- created_order: `examples/test_created_order_request_201.json`

## Lab Rules
- Do not edit the shared contract in `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`.
- Edit only files under `examples/`.

## Specmatic references
- External examples: [https://docs.specmatic.io/features/external_examples](https://docs.specmatic.io/features/external_examples)
- Specmatic Studio: [https://docs.specmatic.io/getting_started/studio_quick_start.html](https://docs.specmatic.io/getting_started/studio_quick_start.html)

## Lab Implementation Phases

### Baseline Phase

Bring the current examples to a fully valid state and ensure all required create-scenario examples are present.

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
[FAIL] Examples: 1 passed and 3 failed out of 4 total
```

Test Run Cmd (Windows PowerShell or CMD)

```shell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
```

Expected output:

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[FAIL] Examples: 1 passed and 3 failed out of 4 total
```

### Studio Phase

Start Studio:

```shell
docker compose --profile studio up
```

In Studio, open `product_search_bff_v6.yaml` from `.specmatic/repos/labs-contracts/common/openapi/order-bff`. You should see three failed examples in the **Examples** tab.

Click on each failed example to see the validation errors and fix them. You can either use the "Fix" button in Studio to automatically fix the issues, or fix the examples manually as shown below.

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

Expected output:
After applying the Studio fixes and generating the missing `201` examples, the following should be seen:

```terminaloutput
[OK] Examples: 6 passed and 0 failed out of 6 total
```

Stop Studio after the fixes and generated examples are saved:

```shell
docker compose --profile studio down -v
```

### Final Phase

Windows (PowerShell or CMD):

```shell
docker run --rm -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest validate
```

Expected output:

```terminaloutput
[OK] Specification product_search_bff_v6.yaml: PASSED
[OK] Examples: 6 passed and 0 failed out of 6 total
```

## Pass Criteria
- `validate` reports `6 passed and 0 failed out of 6 total`.
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
