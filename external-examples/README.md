# Studio Lab: Generate, Validate, Fix External Examples

This lab demonstrates how to work with external examples for an OpenAPI spec in Specmatic Studio.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec and it's example files.

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
[FAIL] Examples: 1 passed and 3 failed out of 4 total
```

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
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples have failed validation.

Click on each failed example to see the validation errors and fix them. You can either fix the examples manually or use the "Fix" button in Studio to automatically fix the issues.

## Re-validate the Examples after fixing in Studio
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
[OK] Examples: 4 passed and 0 failed out of 4 total
```

## Generate Missing Examples for both 201 Response
Using Studio generate examples for both the POST /products 201 and POST /orders 201 endpoint. 

## Re-validate the Examples after Generating Missing Examples in Studio
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
[OK] Examples: 6 passed and 0 failed out of 6 total
```
