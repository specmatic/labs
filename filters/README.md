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
- `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`: shared OpenAPI contract loaded by `specmatic.yaml`.
- `specmatic.yaml`: Specmatic configuration where filters can be persisted.

## Reference
- [Supported filters and operators](https://docs.specmatic.io/contract_driven_development/contract_testing#supported-filters--operators)

## Lab Rules
- Do not edit the shared contract in `.specmatic/repos/labs-contracts/common/openapi/order-bff/product_search_bff_v6.yaml`.
- Focus on filter actions first; config export/update comes later.

## 1. Baseline run (intentional failure)
Run:
```shell
docker compose up --abort-on-container-exit
```

Expected baseline output:
```terminaloutput
Tests run: 136, Successes: 20, Failures: 114, Errors: 2
```

Clean up:
```shell
docker compose down -v
```

## 2. Start Studio
Run:
```shell
docker compose --profile studio up studio
```

Open Studio at `http://127.0.0.1:9000/_specmatic/studio`.

## 3. Run tests in Studio
In Studio, open `specmatic.yaml` from the left sidebar. Click on the `Run Suite` button.

In the Active Tabs on the right sidebar, under the `Test` section, click on `product_search_bff_v6.yaml` to view test results. You should see a large number of failures.

### Task A: Exclude failing scenarios
1. Run tests once to view failures.
2. Click on the `Failed: 114` result button on the top to show only failed tests.
3. Select all listed failed tests.
4. Click `Exclude`.
5. Click `Total` to return to the full list and confirm excluded tests appear greyed out.

Checkpoint after Task A:
- Restart the Mock by clicking on the `Mock` tab and then click on `Run` button.
- Come back to the `Test` tab and click on the `Run` button to re-run tests.
- Expected direction: failures drop sharply and most remaining executed tests are successful.

### Task B: Exclude uncovered 429 response scenarios
1. In results/coverage view, find entries for `429`.
2. Exclude those scenarios.
3. Re-run tests.

Checkpoint after Task B:
- You should see Successes: 20, Failures: 0, Errors: 0, Excluded 4 in Studio.

## 4. Persist filters to config
In Studio:
1. Open `Active Tabs` from the right sidebar.
2. Click `Export as Config`.
3. Confirm `specmatic.yaml` now contains the generated filter expression(s).

Stop Studio:

```shell
docker compose --profile studio down -v
```

## 5. Verify from CLI (with persisted filters)
Run:
```shell
docker compose up --abort-on-container-exit
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
- Baseline run shows `136` tests with many failures.
- After applying and exporting filters, CLI run shows:
  - `Tests run: 20, Successes: 20, Failures: 0, Errors: 0`

## Why this lab matters
- Filters help teams focus on critical scenarios while they triage known failures.
- Coverage can look better after exclusions, so filters should be used intentionally and reviewed regularly.

## Next step
If you are doing this lab as part of an eLearning course, return to the eLearning site and continue with the next module.
