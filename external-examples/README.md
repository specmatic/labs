# Studio Lab: Validate, Fix, and Generate External Examples

## Objective
Use Specmatic Studio to validate external examples, fix contract mismatches, and generate missing examples for `201` responses.

## Prerequisites
- Docker is installed and running.
- You are in `labs/external-examples`.

## Files in this lab
- `specs/simple-openapi-spec.yaml`: OpenAPI contract for the BFF API.
- `examples/*.json`: External examples used for validation.
- `specmatic.yaml`: Specmatic configuration that points to the contract and example directory.

### 1. Run validation and observe the intended failure
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
  --network host \
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
- Validation reports `6 passed and 0 failed out of 6 total` for external examples.

## Reference
- External examples docs: [https://docs.specmatic.io/features/external_examples](https://docs.specmatic.io/features/external_examples)
