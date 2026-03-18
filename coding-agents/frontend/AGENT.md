# Frontend Agent Instructions

Implement the frontend for the API defined by `../products_api.yaml`.

## Stack
- React

## Frontend requirements
- Run on port `4000`.
- In development or mock mode, use `http://localhost:9001` as the API base URL.
- In integration mode, use `http://localhost:3000` as the API base URL.
- Implement:
  - product listing
  - filtering by type
  - product creation
- Show product name, type, and inventory.
- Handle loading and error states.

## Workflow requirements
- Build the UI against a Specmatic mock generated from `../products_api.yaml`.
- Keep mock-mode and real-backend mode easy to switch.
- After mock-mode verification, switch the UI to the real backend and verify one end-to-end flow.

## Constraints
- Do not edit `../products_api.yaml`.
- Do not assume backend-only fields that are not present in the contract.
- Keep the UI simple enough for a workshop demo.
