# Backend Agent Instructions

Implement the backend defined by `../products_api.yaml`.

## Stack
- Node.js
- Express
- In-memory storage only

## Backend requirements
- Run on port `3000`.
- Implement all paths, parameters, and responses from `../products_api.yaml`.
- Return appropriate success and error responses as defined in the contract.
- Keep the implementation simple and easy to inspect in a workshop setting.
- Organize the code so routing and storage logic are easy to follow.

## Verification requirements
- Use Specmatic MCP contract testing against `../products_api.yaml`.
- Use Specmatic MCP resiliency testing against the running backend.
- Do not claim completion until both checks pass.
- Summarize the verification outcome and the commands needed to run the backend locally.

## Constraints
- Do not edit `../products_api.yaml`.
- Do not add a database.
- Do not replace contract verification with manual request checks.
