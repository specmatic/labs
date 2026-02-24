# Studio Lab: Test Filters

## Objective
Use Specmatic test filters to temporarily exclude selected failing scenarios and understand the impact on test results and coverage.

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker is installed and running.
- You are in `labs/filters`.
- Ports `9000` and `9001` are available for Studio.

## Files in this lab
- `specs/simple-openapi-spec.yaml`: OpenAPI contract.
- `specmatic.yaml`: Specmatic configuration where filters can be persisted.

## Reference
- [Supported filters and operators](https://docs.specmatic.io/contract_driven_development/contract_testing#supported-filters--operators)

## Lab Rules
- Do not edit `specs/simple-openapi-spec.yaml`.
- Focus on filter actions first; config export/update comes later.

## 1. Baseline run (intentional failure)
Run:
```shell
docker compose up test --abort-on-container-exit
```

Expected baseline output:
```terminaloutput
Tests run: 134, Successes: 20, Failures: 112, Errors: 2
```

Clean up:
```shell
docker compose down -v
```

## 2. Start Studio
Run:
```shell
docker run --rm \
  --name studio \
  --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```
Windows (PowerShell/CMD) single-line:
```shell
docker run --rm --name studio --network host -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest studio
```

Open Studio at `http://127.0.0.1:9000/_specmatic/studio`.

## 3. Apply filters in Studio (guided)
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar.

Go to the Mock tab and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, set url as `http://localhost:8080`

### Task A: Exclude failing scenarios
1. Run tests once to view failures.
2. Click `Failed: 201` to show only failed tests.
3. Select all listed failed tests.
4. Click `Exclude`.
5. Click `Total` to return to the full list and confirm excluded tests appear greyed out.

Checkpoint after Task A:
- Re-run tests from Studio.
- Expected direction: failures drop sharply and most remaining executed tests are successful.

### Task B: Exclude uncovered 429 response scenarios
1. In results/coverage view, find entries for `429`.
2. Exclude those scenarios.
3. Re-run tests.

Checkpoint after Task B:
- You should see Successes: 21, Failures: 0, Errors: 0, Excluded 7 in Studio.

## 4. Persist filters to config
In Studio:
1. Open `Active Tabs` from the right sidebar.
2. Click `Export as Config`.
3. Confirm `specmatic.yaml` now contains the generated filter expression(s).

Stop Studio by pressing `Ctrl+C` in the terminal where it's running.

## 5. Verify from CLI (with persisted filters)
Run:
```shell
docker compose up test --abort-on-container-exit
```

Expected output:
```terminaloutput
Tests run: 20, Successes: 20, Failures: 0, Errors: 0
```

Clean up:
```shell
docker compose down -v
```

## Pass Criteria
- Baseline run shows `224` tests with many failures.
- After applying and exporting filters, CLI run shows:
  - `Tests run: 20, Successes: 20, Failures: 0, Errors: 0`

## Why this lab matters
- Filters help teams focus on critical scenarios while they triage known failures.
- Coverage can look better after exclusions, so filters should be used intentionally and reviewed regularly.
