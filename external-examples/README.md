# Studio Lab: Validate, Fix, and Generate External Examples

Teams often keep executable examples outside the OpenAPI file so domain teams can update test cases without editing the contract itself. This lab shows how Specmatic validates those external examples and catches drift early.

## Objective
Use Specmatic Studio (and `validate`) to:
1. Reproduce failing external examples.
2. Fix invalid examples.
3. Add missing `201` examples for create APIs.
4. Re-run validation to a clean pass.

## Time required to complete this lab
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/external-examples`.
- Ports `9000` and `9001` are free (for Studio).

## Files in this lab
- `specs/simple-openapi-spec.yaml`: OpenAPI contract for the BFF API.
- `examples/*.json`: External examples validated against the contract.
- `specmatic.yaml`: Specmatic config (contract + examples directory).

## Learner task
Bring external examples to a fully valid state and ensure all required create-scenario examples are present.

## Lab Rules
- Do not edit `specs/simple-openapi-spec.yaml`.
- Edit only files under `examples/`.

## 1. Intentional failure (baseline run)
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

Use Studio to easily fix these spec invalid examples.

### 2. Start Studio
```shell
docker run --rm \
  --name studio \
  -p 9000:9000 \
  -p 9001:9001 \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples have failed validation.

Click on each failed example to see the validation errors and fix them. You can either fix the examples manually or use the "Fix" button in Studio to automatically fix the issues.

### 3. Auto-Fix the 3 failing external examples (tiny actions)
In Studio, update the failing examples:

1. `examples/test_find_available_products_book_200.json`
   - Change `query.to-date` from `"today"` to a valid ISO date (for example `"2025-11-28"`).
2. `examples/test_accepted_product_request.json`
   - Change `body.type` from `"movie"` to one of: `book`, `food`, `gadget`, `other`.
   - Change `body.inventory` from `"five"` to a number (for example `5`).
3. `examples/test_accepted_order_request.json`
   - Add missing required property `count` (for example `2`) in request body.

### 4. Generate missing examples in the same Studio flow
Still in Studio, generate examples for:
- `POST /products` with response `201`
- `POST /orders` with response `201`

### 5. Re-run validation and verify pass state
```shell
docker run --rm \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  validate
```

Expected final output:
```terminaloutput
[OK] Specification simple-openapi-spec.yaml: PASSED
[OK] Examples: 6 passed and 0 failed out of 6 total
```

## Pass Criteria
- `validate` reports `6 passed and 0 failed out of 6 total`.
- Overall validation result is `PASSED`.

## Reference
- External examples: https://docs.specmatic.io/features/external_examples
- Specmatic Studio: https://docs.specmatic.io/documentation/specmatic_studio
