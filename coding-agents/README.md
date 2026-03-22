# Lab: Specmatic as Guardrails for Coding Agents

## Objective
Use any MCP-capable coding agent to build a small full-stack application from an OpenAPI specification, with Specmatic MCP acting as the contract, mock, and verification guardrail throughout the workflow.

## Why this lab matters
Coding agents are fast, but they can drift when they generate code without a strong source of truth. This lab shows a safer loop:

1. Start from an OpenAPI specification.
2. Register the Specmatic MCP server with your coding agent.
3. Build the backend first and verify it against the contract.
4. Build the frontend against a Specmatic mock.
5. Switch the frontend to the real backend and verify one end-to-end flow.

## Time required to complete this lab
20-30 minutes.

## Prerequisites
- Docker is installed and running.
- Node.js 20+ and npm are available on your machine.
- You have an MCP-capable coding agent available, such as Claude Code or Codex.
- You are in `labs/coding-agents`.
- Ports `3000`, `4000`, and `9001` are available.

## Coding Agents Overview Video
[![Watch the video](https://img.youtube.com/vi/UgxxDtE5h_s/hqdefault.jpg)](https://www.youtube.com/watch?v=UgxxDtE5h_s)

## Files in this lab
- `products_api.yaml`: The source-of-truth OpenAPI specification.
- `AGENT.md`: Shared instructions for the coding agent at the project root.
- `backend/AGENT.md`: Backend-specific implementation and verification rules.
- `frontend/AGENT.md`: Frontend-specific implementation and integration rules.

## Who is who in this lab
- Source of truth: `products_api.yaml`
- Coding agent: your MCP-capable coding assistant
- Contract guardrail: Specmatic MCP contract and schema resiliency tools
- Mock provider: Specmatic MCP mock generated from the same OpenAPI specification

## Learner task
Use your coding agent to generate:
- a Node.js and Express backend that satisfies the contract
- a React frontend that works first against the mock, then against the real backend

## Intentional starting state
This lab starts with only an API Spec and guidance files. There is no application implementation yet. The repository is intentionally incomplete so you can see how a coding agent uses Specmatic MCP to build from the contract instead of from guesswork.

## Lab Rules
- Do not edit `products_api.yaml`.
- Keep the API shape defined by the spec as-is.
- Use the coding agent plus Specmatic MCP for verification instead of manually validating with `curl`.
- Build the backend before the frontend.

## Specmatic references
- Specmatic MCP overview: [https://github.com/specmatic/specmatic-mcp-server](https://github.com/specmatic/specmatic-mcp-server)
- Contract testing: [https://docs.specmatic.io/documentation/contract_tests.html](https://docs.specmatic.io/documentation/contract_tests.html)
- Service virtualization: [https://docs.specmatic.io/documentation/service_virtualization_tutorial.html](https://docs.specmatic.io/documentation/service_virtualization_tutorial.html)
- Resiliency testing: [https://docs.specmatic.io/documentation/resiliency_techniques.html](https://docs.specmatic.io/documentation/resiliency_techniques.html)

## Architecture
```text
                    +--------------------+
                    |  products_api.yaml |
                    |  OpenAPI contract  |
                    +---------+----------+
                              |
          +-------------------+-------------------+
          |                                       |
          v                                       v
+----------------------+             +----------------------+
| Specmatic MCP Mock   |             | Specmatic MCP Tests  |
| Port: 9001           |             | Contract + Resiliency|
+----------+-----------+             +----------+-----------+
           |                                      |
           v                                      v
+----------------------+             +----------------------+
| React Frontend       | <---------> | Express Backend      |
| Port: 4000           |             | Port: 3000           |
+----------------------+             +----------------------+
```

## Part A: Register the Specmatic MCP server
Choose one coding agent and register the local Specmatic MCP server.

### Agent setup examples
These examples only cover MCP registration and session startup. The lab flow after that is the same.

#### Claude Code
Register a local stdio server:

```bash
claude mcp add --transport stdio specmatic -- npx -y specmatic-mcp
```

Start Claude Code in this lab folder:

```bash
claude
```

Prompt handling:
- Paste the prompts from Parts B, C, and D directly into the Claude Code session.
- If Claude presents a plan first, review it, then allow execution.
- If Claude asks for MCP approval, approve the `specmatic` server before continuing.

#### Codex
Register a local stdio server:

```bash
codex mcp add specmatic -- npx -y specmatic-mcp
```

Start Codex in this lab folder:

```bash
codex
```

Prompt handling:
- Paste the prompts from Parts B, C, and D directly into the Codex session.
- If Codex shows a plan first, review it, then continue with execution.
- If Codex asks for command approval or MCP usage approval, approve the requested action so it can run the Specmatic workflow.

If you use a different coding agent, register `specmatic-mcp` using that tool's MCP setup flow before continuing.

## Part B: Build and verify the backend
Ask your coding agent to read:
- `AGENT.md`
- `backend/AGENT.md`

Then give it this prompt:

```text
Read AGENT.md and backend/AGENT.md. Build the backend first from products_api.yaml.

Requirements:
- Use Node.js and Express.
- Keep all data in memory.
- Implement the API exactly as defined in products_api.yaml.
- Use Specmatic MCP contract and resiliency checks as the verification loop.
- Do not edit products_api.yaml.
- When finished, tell me what commands to run to start the backend and what Specmatic MCP checks passed.
```

Expected outcome:
- a backend project exists under `backend/`
- the agent has used Specmatic MCP to verify contract compliance
- the backend can run on port `3000`

Checkpoint:
- The backend supports `GET /products?type={type}`.
- The backend supports `POST /products`.
- Contract and resiliency verification both pass.

## Part C: Build the frontend against the mock
Ask your coding agent to read:
- `AGENT.md`
- `frontend/AGENT.md`

Then give it this prompt:

```text
Read AGENT.md and frontend/AGENT.md. Build the frontend against a Specmatic mock generated from products_api.yaml.

Requirements:
- Use React.
- Run the frontend on port 4000.
- In development mode, point the app to the Specmatic mock on port 9001.
- Build product listing, filtering, and product creation.
- Do not edit products_api.yaml.
- When finished, tell me how to start the mock and the frontend, and what user flow you verified.
```

Expected outcome:
- a frontend project exists under `frontend/`
- the app works against a mock on port `9001`
- you can list products by type and create a product from the UI

Checkpoint:
- the frontend can run with the mock without requiring the backend
- one create flow and one list flow work against the mock

## Part D: Switch to the real backend and verify integration
Ask your coding agent to switch the frontend from mock mode to real-backend mode and verify the full flow.

Use this prompt:

```text
Now verify end-to-end integration.

Requirements:
- Run the real backend on port 3000.
- Reconfigure the frontend to use http://localhost:3000 instead of the mock.
- Verify one end-to-end flow that creates a product and then retrieves it through the UI.
- Keep the API contract unchanged.
- Summarize what changed between mock mode and integration mode.
```

Expected outcome:
- the frontend talks to the real backend on port `3000`
- one documented UI flow works end-to-end

## Pass criteria
- Specmatic MCP is registered in your coding agent.
- The backend is generated under `backend/` and passes contract verification.
- The backend passes resiliency verification.
- The frontend is generated under `frontend/` and works against the mock on port `9001`.
- The frontend then works against the real backend on port `3000`.
- You can complete one documented create-and-list product flow through the UI.

## Troubleshooting
- If the coding agent ignores the guidance files, explicitly tell it to read `AGENT.md` and the relevant subfolder `AGENT.md` before writing code.
- If the backend is built but not verified, ask the agent to use Specmatic MCP contract and resiliency tools before it claims completion.
- If the frontend still points to the mock during integration, ask the agent to switch the API base URL to `http://localhost:3000`.
- If `npx` prompts for package installation, rerun the MCP registration command with `-y`.
- If port `3000`, `4000`, or `9001` is busy, stop the conflicting process before retrying.
- If your agent requires explicit permission before using MCP tools, approve the Specmatic MCP server when prompted.

## Optional extension
Ask the coding agent to add:
- a better empty state for filtered results
- basic client-side validation for the create form
- one additional UI check after integration

## What you learned
- A coding agent works better when the OpenAPI contract remains the source of truth.
- Specmatic MCP can keep backend implementation aligned with the contract.
- Specmatic mock lets the frontend move independently before the backend is ready.
- The same contract can drive generation, mocking, contract checks, and integration verification.
