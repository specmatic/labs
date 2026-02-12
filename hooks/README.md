# Case Insensitive API Testing

A minimal lab that validates API compatibility between:

- a **PascalCase** service (`pascalCase.yaml`) - expects all the API request and response field names to be in PascalCase
- a **camelCase** service (`camelCase.yaml`) - expects all the API request and response field names to be in camelCase

When `PascalCase` service is tested against `camelCase` service, the request and response field names need to be transformed from PascalCase to camelCase before hitting the `camelCase` service.

The objective of this lab is to understand how you can uses Specmatic hook adapters to translate request/response field names between the two cases.

## Run the test

### 1. Via Studio:

#### Step 1: Start the studio
```bash
docker run --rm \
  --name studio \
  -v "$PWD":/usr/src/app \
  -v "$HOME/.specmatic":/root/.specmatic \
  -p 9000:9000 \
  -p 9001:9001 \
  specmatic/enterprise:latest \
  studio
```

#### Step 2: Open the studio in your browser

Open the studio in your browser at `http://localhost:9000/_specmatic/studio`

#### Step 3: Open `camelCase.yaml` in the studio

Click on the `camelCase.yaml` link in the studio to open the contract in the studio.

#### Step 4: Start the mock

Click the `Mock` tab  and then click on the `Run` button to start the mock.

#### Step 5: Open `pascalCase.yaml` in the studio

Click on the `pascalCase.yaml` link in the studio to open the contract in the studio.

#### Step 6: Start the test

Click the `Test` tab  and then click on the `Run` button to start the test.

You should see 1 test fail because of the mismatch in the case of the field names.

### 2. Via Docker Compose:

```bash
docker compose up
```
You should see 1 test fail because of the mismatch in the case of the field names.

## Goal of this lab

Your goal is to make the test pass by using Specmatic hook adapters to translate request/response field names between the two cases.

### Verify you've met the goal

Run the test again to verify that 1 test is passing.

### Notes

- Reports are written to `build/reports/specmatic/`
