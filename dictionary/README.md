# Studio Lab: Dictionary to Generate Domain-Aware Request/Response Payloads

This lab demonstrates how to use Specmatic's Dictionary feature to generate domain-aware request/response payloads for contract testing and service virtualization.

## Time required to complete this lab:
10-15 minutes.

## Files in this lab
- `specs/simple-openapi-spec.yaml` - OpenAPI spec for the BFF API. This is the main contract that we will be working with in this lab.
- `examples/*.json` - External examples for the BFF API. These examples have some issues we'll fix them
- `specmatic.yaml` - Specmatic config file that defines the Spec, and it's example files.

## Run loop test using Docker
```shell
docker compose up
```

### Output
```terminaloutput
Tests run: 3, Successes: 0, Failures: 3, Errors: 0
```

### Root cause of the failed tests
Tests expect a specific value in the response body, but the mock is generating random values as it does not have examples. We will use dictionary feature to ensure the mock only use specific values defined in the dictionary file to generate the response.

## Using Dictionary to fix the examples

```shell
docker run --rm specmatic/enterprise --help
```

Then try
```shell
docker run --rm specmatic/enterprise examples --help
```

Then try
```shell
docker run --rm specmatic/enterprise examples dictionary --help
```

Finally
```shell
docker run --rm -v .:/usr/src/app specmatic/enterprise examples dictionary --examples-dir examples --spec-file specs/simple-openapi-spec.yaml --out specs/dictionary.yaml
```

This command will read the examples from the `examples` directory, extract the values for the fields defined in the OpenAPI spec, and generate a dictionary file `specs/dictionary.yaml` that contains the placeholder values for those fields. We can then use this dictionary file in our mock to ensure that only allowed values are being returned by the mock, which will fix the failed tests.

### How to pass the Dictionary file to the mock
In the `specmatic.yaml` file, we can specify the dictionary file to be used by the mock by adding the following lines under the `dependencies/services/service` section:
```yaml
  data: 
    dictionary: 
      path: specs/dictionary.yaml
```

## Re-run loop test using Docker after fixing the examples using dictionary
```shell
docker compose up
```

### Output
```terminaloutput
Tests run: 3, Successes: 3, Failures: 0, Errors: 0
```