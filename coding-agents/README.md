# Lab: Specmatic as Guardrails for Coding Agents

## Objective
Use any MCP-capable coding agent to build a small full-stack application from an OpenAPI specification, with Specmatic MCP acting as the contract, mock, and verification guardrail throughout the workflow.

## Why this lab matters
Coding agents are fast, but they can drift when they generate code without a strong source of truth. This lab shows a safer loop:

1. Start from an OpenAPI specification.
2. Register the Specmatic MCP server with your coding agent.
3. Give the agent one goal referencing `AGENTS.md`.
4. Let the agent follow the build and verification workflow.
5. Review the results against the pass criteria below.

## Time required to complete this lab
20-30 minutes.

## Prerequisites
- Docker is installed and running.
- Pull the latest specmatic docker image:

```bash
docker pull specmatic/enterprise-snapshots:latest
```

- Node.js 20+ and npm are available on your machine.
- You have an MCP-capable coding agent available, such as Claude Code or Codex.
- You are in `labs/coding-agents`.
- Ports `3000`, `4000`, and `9001` are available.

## Coding Agents Overview Video
[![Watch the video](https://img.youtube.com/vi/UgxxDtE5h_s/hqdefault.jpg)](https://www.youtube.com/watch?v=UgxxDtE5h_s)

## Files in this lab
- `products_api.yaml`: The source-of-truth OpenAPI specification.
- `AGENTS.md`: Shared application requirements, backend and frontend guidance, and completion criteria.

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
- Follow the application requirements and workflow in `AGENTS.md`.

## Specmatic references
- Specmatic MCP overview: [https://docs.specmatic.io/features/specmatic_mcp](https://docs.specmatic.io/features/specmatic_mcp)
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

## Register the Specmatic MCP server
Choose one coding agent and register the local Specmatic MCP server.

### Agent setup examples
These examples only cover MCP registration and session startup. The lab flow after that is the same.

#### Claude Code
Register a local stdio server:

```bash
claude mcp add specmatic -- docker run --rm -i -v ".:/usr/src/app" specmatic/specmatic mcp server
```

Start Claude Code in this lab folder:

```bash
claude
```

Prompt handling:
- Paste the plain-text prompt into the Claude Code session.
- If Claude presents a plan first, review it, then allow execution.
- If Claude asks for MCP approval, approve the `specmatic` server before continuing.

#### Codex
Install the Codex plugin, which supplies the Specmatic workflow and MCP tools:

```bash
pwd > plugins/specmatic/.lab-directory
codex plugin marketplace add .
codex plugin add specmatic@specmatic-labs
```

Start a fresh Codex session in this lab folder:

```bash
codex --no-daemon
```

Prompt handling:
- Set the goal from below in the Codex session.
- If Codex shows a plan first, review it, then continue with execution.
- If Codex asks for command approval or MCP usage approval, approve the requested action so it can run the Specmatic workflow.


#### Gemini
If you are using Gemini Agent through Antigravity, paste this MCP config into the agent's config file used for MCP servers.

```json
{
  "mcpServers": {
    "specmatic": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        ".:/usr/src/app",
        "specmatic/specmatic",
        "mcp",
        "server"
      ]
    }
  }
}
```

If you use a different coding agent, register `specmatic mcp` using that tool's MCP setup flow before continuing.


## Build and verify the application

In Codex, set one goal:

```text
/goal Build the complete application described in AGENTS.md. Keep working until all completion criteria in AGENTS.md are verified, then report the results and how to run the application.
```

Review the agent's evidence against the pass criteria below.

## Pass criteria
- The backend is generated under `backend/` and passes contract verification.
- The backend passes resiliency verification.
- The frontend is generated under `frontend/` and works against the mock on port `9001`.
- The frontend then works against the real backend on port `3000`.
- You can complete one documented create-and-list product flow through the UI.

## Check MCP readiness before starting the goal

Before submitting the build goal:

1. Run `/mcp` in that same Codex session and confirm `specmatic-enterprise` is connected.
2. Ask the agent to call Specmatic `get_runtime_info`. A successful tool call is the readiness gate; an enabled plugin or running Docker container is insufficient.
3. If the tool is missing, resolve MCP startup first. Do not silently substitute CLI verification when demonstrating this lab's MCP workflow.

The MCP launcher publishes host port 9001 for its mock. Run only one lab MCP session using that port at a time. Inspect `docker ps` to identify an older owner and close that session normally before starting another. Do not stop unrelated containers.

A previous investigation found an explicit Docker port-9001 collision during one startup, and Codex later logged `omitting MCP server without an exact ready client` for the build session. A separate session successfully initialized the server and received all 13 tools. These observations establish distinct port ownership and session readiness problems; they do not establish a Specmatic schema error or prove that the startup mitigation fixes the session binding problem.

If readiness still fails, collect the Codex MCP startup error and the relevant container's logs. `omitting pending optional MCP server` indicates startup timing; `without an exact ready client` means the session cannot use a matching ready connection and requires further client-side diagnosis. Restart a fresh local session and repeat the actual tool-call gate.

Reference: [Official Codex MCP configuration and startup settings](https://developers.openai.com/codex/mcp).

## Troubleshooting
- If the coding agent ignores the guidance files, explicitly tell it to read the lab’s root `AGENTS.md` before writing code.
- If the backend is built but not verified, ask the agent to use Specmatic MCP contract and resiliency tools before it claims completion.
- If the frontend still points to the mock during integration, ask the agent to switch the API base URL to `http://localhost:3000`.
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

## Next step
If you are doing this lab as part of an eLearning course, r~eturn to the eLearning site and continue with the next module.

## Generated application

See [APPLICATION.md](APPLICATION.md) for verified startup commands, mock and integration modes, test results, and the UI demo flow.
