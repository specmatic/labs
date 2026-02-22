# Request/Response Adapters Lab

## Objective
Make a PascalCase contract test pass against a camelCase mock service by transforming request and response field names using Specmatic data adapters.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/data-adapters`.

## Files in this lab
- `pascalCase.yaml`: Contract used by the test runner (PascalCase fields).
- `camelCase.yaml`: Contract used by the mock service (camelCase fields).
- `specmatic.yaml`: Test + mock wiring where you will configure hooks.
- `hooks/pre_specmatic_request_processor.sh`: Converts outgoing request keys from PascalCase to camelCase.
- `hooks/post_specmatic_response_processor.sh`: Converts incoming response keys from camelCase to PascalCase.

## Reference
- Processor hooks configuration and usage: [https://docs.specmatic.io/documentation/configuration.html#hooks](https://docs.specmatic.io/documentation/configuration.html#hooks)
- Processor hooks concept: [https://docs.specmatic.io/features/hooks/processor_hooks](https://docs.specmatic.io/features/hooks/processor_hooks)

## Lab Rules
- Do not edit `pascalCase.yaml` or `camelCase.yaml`.
- Do not change `docker-compose.yaml`.
- Fix the mismatch only by wiring the existing hook scripts in `specmatic.yaml`.

## 1. Baseline run (intentional failure)
Run:
```bash
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 1, Successes: 0, Failures: 1, Errors: 0
```

You will see request mismatch errors because `RequestQuery` / `RequestKey` are sent to a mock that expects `requestQuery` / `requestKey`.

## How the loop test works
This lab runs a consumer-test against a mocked provider:

- Consumer side (`test` service):
  - Uses `pascalCase.yaml`
  - Sends requests with PascalCase fields
  - Expects responses with PascalCase fields
- Provider side (`mock` service):
  - Uses `camelCase.yaml`
  - Accepts and returns camelCase fields

Why it fails first:
- Consumer and provider use different field naming conventions.
- Without adapters, the request/response shapes do not match.

What you are fixing:
- Transform request fields before they hit the mock.
- Transform response fields before assertion in the test runner.

Clean up:
```bash
docker compose down -v
```

## 2. Configure hooks in `specmatic.yaml`
Add the following block directly under dependencies in `specmatic.yaml`:

```yaml
data:
  adapters:
    pre_specmatic_request_processor: ./hooks/pre_specmatic_request_processor.sh
    post_specmatic_response_processor: ./hooks/post_specmatic_response_processor.sh
```

Why both hooks are needed:
- `pre_specmatic_request_processor`: adapts PascalCase request fields to camelCase before sending to mock.
- `post_specmatic_response_processor`: adapts camelCase mock response fields back to PascalCase before assertion.

## 3. Ensure hook scripts are executable
Run:
```bash
chmod +x hooks/pre_specmatic_request_processor.sh hooks/post_specmatic_response_processor.sh
```

## 4. Re-run test
Run:
```bash
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Clean up:
```bash
docker compose down -v
```

## Windows Notes
- If you use PowerShell or CMD, `chmod` may not work. Use Git Bash for this step, or run:
```powershell
git update-index --chmod=+x hooks/pre_specmatic_request_processor.sh hooks/post_specmatic_response_processor.sh
```
- Ensure hook files use LF line endings (not CRLF). In Git Bash:
```bash
sed -i 's/\r$//' hooks/pre_specmatic_request_processor.sh hooks/post_specmatic_response_processor.sh
```
- If the test still fails with the same `RequestQuery/requestQuery` mismatch after adding adapters, it usually means hook scripts were not executed. Re-check execute bit and LF line endings.

## 5. Verify in Studio (Optional)
Start Studio:
```bash
docker run --rm \
  --name studio \
  -v .:/usr/src/app \
  -p 9000:9000 \
  -p 9001:9001 \
  specmatic/enterprise:latest \
  studio
```
Open `http://127.0.0.1:9000/_specmatic/studio`, open `specmatic.yaml`, and click `Run Suite`.

## Pass Criteria
- Baseline run fails with `1` failed test.
- After hooks are configured, run passes with `1` successful test.

## Notes
- Reports are written to `build/reports/specmatic/`.
