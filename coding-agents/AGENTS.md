# Project instructions

## Goal
Build a complete application from `products_api.yaml`. Treat this contract as the
source of truth and do not edit it. Paths below are relative to this lab folder.

## Build order
1. Build the backend and pass contract and resiliency tests before moving on
   to the frontend.
2. Build the frontend against a spec-driven mock generated from the contract.
   Verify product creation and listing through the UI independently of the backend.
3. Switch the frontend to the real backend, create a product through the UI,
   and confirm it appears in the UI's list.

## Backend
- Use Node.js and Express in `backend/`, listening on port `3000`.
- Keep all data in memory; do not add a database.
- Implement all paths, parameters, and success and error responses in the contract.

## Frontend
- Use React in `frontend/`, listening on port `4000`.
- Support product listing, filtering by type, and product creation.
- Display product name, type, and inventory; handle loading and error states.
- Use `http://localhost:9001` as the API base URL in mock mode and
  `http://localhost:3000` in integration mode. Keep switching modes easy.

## Implementation quality
- Keep the implementation small, focused, and easy to follow; avoid duplicated logic and unnecessary abstractions.
- Do not add endpoints, response statuses, or product behavior beyond the requirements.
- Keep environment-specific configuration outside application logic.
- Keep production code free of test-only behavior.
- Add focused tests for application behavior not established by contract checks,
  such as create-and-list persistence and filtering.
- Keep application build, test, run, and configuration documentation aligned
  with the implementation.

## Completion
- Report verification results and commands to start the backend, mock, and frontend
  in each mode.
