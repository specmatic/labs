# Specmatic Workshop Labs
Contains all the Labs used during the Specmatic hands-on Workshop

## Time required to complete this lab:
10-15 minutes.

## Prerequisites
- Docker Engine installed and running on your machine
- An IDE (IntelliJ, VS Code, etc.) 


## Getting Started
Clone the repository to your local machine: 
```bash 
git clone https://github.com/specmatic/labs
```

## Lab Structure 
This is a mono-repo. Each lab is self-contained and organized in a separate directory with its own README file containing instructions and code examples. 

## 3-Day Workshop Schedule 
- Overview
  - Independent Development and Deployment 
  - Test Pyramid - Contract Testing, API Testing, Workflow Testing 
  - Various Types of Contract Testing (CDCT, PDCT & API Design First)
  - Specification (OpenAPI, AsyncAPI, ProtoBuf, GraphQL SDL, WSDL, Arazzo)
  - Contract Driven Development (CDD) in Action Demo - Using [Order-BFF](order-bff/README.md) as an example
- [Contract Testing](quick-start-contract-testing/README.md)
  - API Contract Test
  - Using Inline examples as test data
  - Using External examples as test data
- [Intelligent service virtualization](quick-start-mock/README.md)
  - Inline Examples as mock data 
  - External examples as mock data
- [AsyncAPI Contract Testing](quick-start-async-contract-testing/README.md)
- Examples
  - [Generate, Validate and Fix examples](external-examples/README.md)
  - [Partial examples](partial-examples/README.md)
  - [Domain-aware requests using Dictionary](dictionary/README.md)
  - [Response Templating via Direct substitution and Data lookup](response-templating/README.md)
- Specmatic Features
  - [Filters](filters/README.md)
  - [Request/Response Adapters](data-adapters/README.md)
  - [Overlays](overlays/README.md)
  - [Workflow within the Same Spec](workflow-in-same-spec/README.md)
  - [Kafka and Avro Schema](kafka-avro/README.md)
  - [Async Event Flow](async-event-flow/README.md)
  - [Running Contract Tests and Mocks in CI](async-event-flow/README.md)
- More types of Testing
  - [Schema Resiliency Testing](schema-resiliency-testing/README.md)
  - [API Resiliency Testing](api-resiliency-testing/README.md)
  - [API Security Schemes](api-security-schemes/README.md)
  - [API Workflow Testing](arazzo-workflow-testing/README.md)

## Additional Resources 
For more information on Specmatic and its features, please refer to the official documentation: [Specmatic Documentation](https://docs.specmatic.in)

Happy learning!
