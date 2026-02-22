# Studio Lab: Test Filters

This lab demonstrates how to use Filters to skipping running certain tests and what is the implication of the same on the coverage report.

## Time required to complete this lab:
10-15 minutes.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `specmatic.yaml` - Specmatic config file that defines the Spec, and it's example files.

## Start Studio using Docker
```shell
docker run --rm \
  --name studio \
  --network host \
  -v .:/usr/src/app \
  -v ../license.txt:/specmatic/specmatic-license.txt:ro \
  specmatic/enterprise:latest \
  studio
```

## Loop Test

### 1. Loop Test in Studio
In Studio, open the [simple-openapi-spec.yaml](specs/simple-openapi-spec.yaml) file from the left sidebar, and you will see that 3 examples are valid.

Go to the Mock tab and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, set url as `http://localhost:8080` and click on the "Run" button to run the tests against the mock server.

You should see 

```terminaloutput
Tests run: 224, Successes: 21, Failures: 201, Errors: 2
```

### 2. Loop Test using CLI
```shell
docker compose up test --abort-on-container-exit
```
This will start the mock server and run the tests against it. You should see the same results in the terminal output as you did in Studio:

```terminaloutput
Tests run: 224, Successes: 21, Failures: 201, Errors: 2
```

Clean up
```shell
docker compose down
```

## Goal of this lab
The goal of this lab is to use filters to temporarily skip all the failing tests.

### Use filters in Studio
In the Test tab, 
1. Filter all the failing tests by clicking on the `Failed: 201` button. This will show you only the failing tests in the test results.
2. Now, select the checkboxes next to the failing tests and click on the "Exclude" button to exclude them from the test run.
3. Now, click on the `Total: 225` button to show all the tests again. You will see that the 201 failing tests are gray out. Which means that they are excluded from the test run. 
4. Now, click on the "Run" button again to run the tests against the mock server. You should see that only the 21 successful tests are run and all the failing tests are skipped.
5. Now, you should see total 22 tests ran (21 successful + 1 skipped) and 0 failures in the test results.
6. Now, let's exclude the 429 response code which is showing as remark `Not Covered`
7. Now, run the tests against. You should see that only the 21 successful tests are run and all the failing and skipped tests are not executed.
8. You will also see that the coverage now shows 100% as all the tests that were not covered are now skipped.

Now if we want to preserve these filters for future test runs, we need to update the `specmatic.yaml` file to include the filters.

From the `Active Tabs` section in the right sidebar, click on the `Export as Config` to export the current filters as config. This will update the `specmatic.yaml` file to exclude the end points we filtered out.

Look at the [Supported Filters & Operators](https://docs.specmatic.io/contract_driven_development/contract_testing#supported-filters--operators) and update the `specmatic.yaml` file to include the filters that you want to apply for future test runs. 

Now run:
```shell
docker compose up test --abort-on-container-exit
```
You should see

```terminaloutput
Tests run: 21, Successes: 21, Failures: 0, Errors: 0
```
Clean up
```shell
docker compose down
```