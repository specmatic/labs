# Quick Start

<!-- TOC -->
* [Quick Start](#quick-start)
  * [OpenAPI for HTTP REST](#openapi-for-http-rest)
    * [Using Specmatic Open Source Version](#using-specmatic-open-source-version)
      * [Start the Mock Server](#start-the-mock-server)
      * [Run Contract Tests](#run-contract-tests)
    * [Using Specmatic Enterprise Version](#using-specmatic-enterprise-version)
      * [CLI](#cli)
        * [Start the Mock Server](#start-the-mock-server-1)
        * [Creating a simple config file (Specmatic.yaml)](#creating-a-simple-config-file-specmaticyaml)
        * [Start the Mock Server using Specmatic Config](#start-the-mock-server-using-specmatic-config)
        * [Update Config for running Contract Test](#update-config-for-running-contract-test)
        * [Run Contract Tests](#run-contract-tests-1)
      * [Studio](#studio)
  * [AsyncAPI for Events](#asyncapi-for-events)
    * [Studio](#studio-1)
  * [Update Specmatic Config with AsyncAPI](#update-specmatic-config-with-asyncapi)
  * [Running Everything](#running-everything)
<!-- TOC -->

## OpenAPI for HTTP REST

### Using Specmatic Open Source Version

#### Start the Mock Server

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/specmatic mock ./specs/service.yaml
```

#### Run Contract Tests

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/specmatic test ./specs/service.yaml --testBaseURL=http://localhost:9000
```

You should see:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Stop the Mock Server before moving to the next section.

### Using Specmatic Enterprise Version

#### CLI

##### Start the Mock Server

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/enterprise mock ./specs/service.yaml
```

#### Run Contract Tests

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/enterprise test ./specs/service.yaml --testBaseURL=http://localhost:9000
```

You should see the same output as the open source version:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

Stop the Mock Server before moving to the next section.

#### Creating a simple config file (Specmatic.yaml)
To avoid passing the same arguments in the command line every time, we can create a simple config file called `specmatic.yaml` to specify these details and more.

Create a file called `specmatic.yaml` under quick-start folder with the following content:
```yaml
version: 3

dependencies:
  services:
    - service:
        definitions:
          - definition:
              source:
                filesystem:
                  directory: specs
              specs:
                - service.yaml
        runOptions:
          openapi:
            host: localhost
            port: 8080
```
##### Start the Mock Server using Specmatic Config

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/enterprise mock
```
You should see 
```terminaloutput
Mock server is running on the following URLs:
- http://localhost:8080 serving endpoints from specs:
        1. specs/service.yaml
```

Note: since we've specified the port at `8080` the server has started on the specified port.
Also note that in the command line argument we did not have to pass `./specs/service.yaml` because that is already mentioned in the config.

##### Update Config for running Contract Test
Add the following `systemUnderTest` section on line 3 of the `specmatic.yaml` file

```yaml
systemUnderTest:
  service:
    definitions:
      - definition:
          source:
            filesystem:
              directory: specs
          specs:
            - service.yaml
    runOptions:
      openapi:
        host: host.docker.internal
        port: 8080
```

##### Run Contract Tests

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/enterprise test
```

You should see:

```terminaloutput
Specmatic Enterprise v1.x.x
Specmatic Core v2.x.x

Loading config file ./specmatic.yaml
API Specification Summary: /usr/src/app/specs/service.yaml
  OpenAPI Version: 3.0.1
  API Paths: 1, API Operations: 1

Endpoints API and SwaggerUI URL were not exposed by the application, so cannot calculate actual coverage

Using Specmatic Open Source license initialized from jar:file:/usr/local/share/enterprise/enterprise.jar!/specmatic-default-trial-license.txt

--------------------
  Request to http://host.docker.internal:8080 at 2026-2-17 5:25:41.768
    GET /pets/1
    Specmatic-Response-Code: 200
    Host: host.docker.internal:8080
    Accept-Charset: UTF-8
    Accept: */*
    Content-Type: NOT SENT

  Response at 2026-2-17 5:25:41.836
    200 OK
    Vary: Origin
    X-Specmatic-Result: success
    Content-Length: 94
    Content-Type: application/json
    Connection: keep-alive
    
    {
        "id": 1,
        "name": "Scooby",
        "type": "Golden Retriever",
        "status": "Adopted"
    }

 Scenario: GET /pets/(petid:number) -> 200 with the request from the example 'SCOOBY_200_OK' has SUCCEEDED
 
Tests run: 1, Successes: 1, Failures: 0, Errors: 0 
```

Note: You don't need to pass `./specs/service.yaml --testBaseURL=http://localhost:9000` in the CLI argument anymore as it is already present in the config

Stop the Mock Server and delete the [specmatic.yaml](specmatic.yaml) before moving to the next section.

#### Studio

Start Studio

```shell
docker run --rm --network host -v .:/usr/src/app specmatic/enterprise studio
```

You should see:
```terminaloutput
Specmatic Enterprise v1.x.x
Specmatic Core v2.x.x

System Properties received by Specmatic Studio:
Specmatic Studio is running on http://localhost:9000/_specmatic/studio, press Ctrl+C to stop
```

Open [Specmatic Studio](http://localhost:9000/_specmatic/studio)

In Studio, open the [service.yaml](specs/service.yaml) file from the left sidebar.

Go to the Mock tab, enter port `8080` and click on the "Run" button to start the mock server on port 8080

Then go to the Test tab, make sure the URL in the text box shows `http://localhost:8080` and click on the "Run" button to run the tests against the mock server.

You should see

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

### Export Specmatic Config from Studio
In the `Active Tabs` on your right hand side, click on the `Export as config` to export the `specmatic.yaml` with OpenAPI related changes.

Now stop the mock server and open the new generated `specmatic.yaml` file.

Now you should be able to run both the mock server and contract testing by simply clicking the "Run Suite" button.

You should see the same output as before when you run the tests:

```terminaloutput
Tests run: 1, Successes: 1, Failures: 0, Errors: 0
```

## AsyncAPI for Events

AsyncAPI is only supported in Enterprise version of Specmatic.

### Studio

In Studio, open the [async.yaml](specs/async.yaml) file from the left sidebar.

Go to the Mock tab, enter 9092 port and click on the "Run" button to start the Kafka mock server on port 9092

Then go to the Test tab, and click on the "Run" button to run the tests against the mock server.

You should see

```terminaloutput
Tests run: 2, Successes: 2, Failures: 0, Errors: 0
```

## Update Specmatic Config with AsyncAPI

In the `Active Tabs` on your right hand side, click on the `Export as config` to update the specmatic.yaml with AsyncAPI related changes.

Stop all the mocks.

## Running Everything one shot
In Studio, open the updated [specmatic.yaml](specmatic.yaml) file from the left sidebar, and click on the "Run Suite" button to run OpenAPI and AsyncAPI tests against their respective mock.

You can go to each of the Tests from the `Active Tabs` and see the results of both OpenAPI and AsyncAPI tests.