# Request/Response Adapters Lab

A minimal lab that validates API compatibility between:

- a **PascalCase** service (`pascalCase.yaml`) - expects all the API request and response field names to be in PascalCase
- a **camelCase** service (`camelCase.yaml`) - expects all the API request and response field names to be in camelCase

When `PascalCase` service is tested against `camelCase` service, the request and response field names need to be transformed from PascalCase to camelCase before hitting the `camelCase` service.

The objective of this lab is to understand how you can use Specmatic adapters to translate request/response field names between the two cases.

## Run the test

### 1. Via Studio:

#### Step 1: Start the studio
```bash
docker run --rm \
  --name studio \
  --network host \
  -v .:/usr/src/app \
  specmatic/enterprise:latest \
  studio
```

#### Step 2: Open the studio in your browser

Open the studio in your browser at `http://localhost:9000/_specmatic/studio`

#### Step 3: Run Test Suite

Click on the `specmatic.yaml` file in Studio and then click on the `Run Suite` button to run the test suite. 

You should see 1 test fail because of the mismatch in the case of the field names.

### 2. Via Docker Compose:

```bash
docker compose up
```
You should see 1 test fail because of the mismatch in the case of the field names.

## Goal of this lab

Your goal is to make the test pass by using Specmatic adapters to translate request/response field names between the two cases.

Learn more about request/response adapters here: https://docs.specmatic.io/features/hooks/processor_hooks

### Verify you've met the goal

Run the test again to verify that 1 test is passing.

### Notes

- Reports are written to `build/reports/specmatic/`
