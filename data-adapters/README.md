# Request/Response Adapters Lab

## Objective
Understand why a client fails against a mock, and how Specmatic data adapters can help you temporarily adapt provider service's interface to the consumer's expected interface till the provider fixes their specification.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/data-adapters`.

## Architecture
- `camel-case-service` (Specmatic mock): serves `camelCase.yaml` on `http://127.0.0.1:9090`
- `ui` service (Nginx): serves a small web page on `http://127.0.0.1:8080`
- Browser UI sends a PascalCase request to camel-case-service, which expects request in camelCase

## Files in this lab
- `camelCase.yaml`: Provider's Contract used by us to start a mock service to emulate the real provider.
- `specmatic.yaml`: Specmatic configuration.
- `ui/index.html`: Simple UI that sends PascalCase query/header/body fields.
- `ui/default.conf`: Nginx config that serves UI and proxies `/test` to the mock.
- `hooks/pre_specmatic_request_processor.sh`: Converts outgoing request keys from PascalCase to camelCase.
- `hooks/post_specmatic_response_processor.sh`: Converts incoming response keys from camelCase to PascalCase.

## Reference
- Processor hooks configuration: [https://docs.specmatic.io/documentation/configuration.html#hooks](https://docs.specmatic.io/documentation/configuration.html#hooks)
- Processor hooks concept: [https://docs.specmatic.io/features/hooks/processor_hooks](https://docs.specmatic.io/features/hooks/processor_hooks)

## Lab Rules
- Do not edit `camelCase.yaml`.
- Do not change `docker-compose.yaml`.
- Do not touch the `ui/index.html`.
- Fix the mismatch only by wiring the existing hook scripts in `specmatic.yaml`.

## 1. Start mock + UI
Run:
```bash
docker compose up
```

Check services:
```bash
docker compose ps
```

## 2. Trigger the mismatch from browser (intentional failure)
1. Open `http://127.0.0.1:8080`.
2. Keep default values and click **Submit** button.
3. Observe a 400 bad-request response in the result panel.

Why it fails:
- The UI sends PascalCase fields (`RequestQuery`, `RequestHeader`, `RequestKey`).
- The provider service (mock in our case) expects camelCase fields (`requestQuery`, `requestHeader`, `requestKey`).

This fail-first behavior is expected in this lab.

## 3. Cleanup
Run:
```bash
docker compose down -v
```
## 4. Configure hooks in `specmatic.yaml`
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

## 5. Ensure hook scripts are executable
Run:
```bash
chmod +x hooks/pre_specmatic_request_processor.sh hooks/post_specmatic_response_processor.sh
```

## 6. Restart mock + UI
Run:
```bash
docker compose up
```

## 7. Trigger the matching request/response from browser
1. Open `http://127.0.0.1:8080`.
2. Keep default values and click **Submit** button.
3. Observe a 200 response in the result panel.

## 8. Cleanup
Run:
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

## 9. Verify in Studio (Optional)
Start Studio:
```bash
docker compose --profile studio up -d studio ui
```
1. Open `http://127.0.0.1:9000/_specmatic/studio`, 
2. Open `camelCase.yaml` and go to the `Mock` tab, enter 9090 as the port and start the mock by clicking on the `Run` button.
3. Open `http://127.0.0.1:8080`.
4. Keep default values and click **Submit** button.
5. Observe a 200 response in the result panel.
6. Go to the `Mock` tab and look at the request and response payloads. You should see how the data adapters have transformed the field names in both directions.

## 10. Cleanup
Run:
```bash
docker compose --profile studio down -v
```
