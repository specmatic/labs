# Project Agent Instructions

This project demonstrates contract-driven app development with any MCP-capable coding agent using Specmatic MCP.

## Goal
Build a complete application from `products_api.yaml` without changing the contract.

## Build order
1. Backend first
2. Frontend against mock
3. Frontend against real backend

## Non-negotiable rules
- Treat `products_api.yaml` as the source of truth.
- Do not edit `products_api.yaml`.
- Use Specmatic MCP for verification instead of ad hoc manual API checks.
- Keep the backend on port `3000`.
- Keep the frontend on port `4000`.
- Keep the Specmatic mock on port `9001`.

## Expected deliverables
- A Node.js and Express backend in `backend/`
- A React frontend in `frontend/`
- Environment-aware frontend configuration so the UI can switch between mock and real backend
- A short summary of the verification steps performed with Specmatic MCP

## Workflow expectations
- Plan before making broad changes.
- Build the backend to satisfy the contract before creating the frontend.
- Use the mock for frontend development isolation.
- Verify one end-to-end flow after switching the frontend to the real backend.

## API summary
`products_api.yaml` defines:
- `GET /products?type={type}` returning a list of products
- `POST /products` creating a new product and returning an id

Supported product types:
- `book`
- `food`
- `gadget`
- `other`

Product fields:
- `name`
- `type`
- `inventory`
