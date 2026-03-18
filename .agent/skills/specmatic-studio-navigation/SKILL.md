---
name: specmatic-studio-navigation
description: Navigate Specmatic Studio, including how to open specs from the left file tree, switch between Examples, Mock, Test, and Spec tabs, generate examples, run tests against a given service url, and inspect artifacts created by Studio. Use when asked to reproduce or debug behavior through Studio's web UI.
---
This repo contains a series of labs that demonstrate various features of Specmatic. Each lab is self-contained and organized in a separate directory, with its own README file containing instructions and code examples.

# Specmatic Studio Navigation

Use this skill when the task requires driving Specmatic Studio through its web UI instead of only using CLI commands.

## Quick Start

- Go through the instructions in the lab's README to set up the environment and understand the expected behavior.
- Check the command in README to see how to start Studio from the lab directory. Usually it would be something like:
  `docker run --rm --network host -v .:/usr/src/app -v ../license.txt:/specmatic/specmatic-license.txt:ro specmatic/enterprise:latest studio`
- Open `http://127.0.0.1:9000/_specmatic/studio`

## Open A Spec

- Hover the small chevron on the left edge to expand the file tree.
- In the tree, click the folder expander to open a directory. Clicking the folder title may only select it.
- Open `specs`, then select the target spec such as `service.yaml`.
- For OpenAPI specs, the screen usually opens on the `Examples` tab.

## Tab Behavior

- `Examples`: generates or validates examples. In OpenAPI flows this content is rendered inside an iframe backed by `http://localhost:9001/_specmatic/examples`.
- `Mock`: starts a mock server for the loaded spec.
- `Test`: runs contract tests against a service using the service URL as per instructions.
- `Spec`: edits the loaded specification.

## Example Generation for OpenAPI

1. Open the spec from the left tree.
2. In `Examples`, click `Generate`.

## Test Execution for OpenAPI

1. Open the spec from the left tree.
2. Switch to `Test`.
3. Set the base URL explicitly. Prefer `http://127.0.0.1:<port>` over `http://localhost:<port>` when reproducing local networking issues.
4. Click `Run`.

## Starting a Mock for OpenAPI

1. Open the spec from the left tree.
2. Switch to `Mock`.
3. Set the port explicitly as per the instructions in the README.
4. Click `Run`.

## Running a Loop Test for OpenAPI

1. Open the spec from the left tree.
2. Start a Mock server first by switching to `Mock`, setting the port, and clicking `Run`.
3. Then run tests against the Mock server by switching to `Test`, setting the base URL to the Mock server's URL, and clicking `Run`.

## What To Inspect

- Studio container output:
  confirms when specs load, examples are written, mock started and tests run.
- Service logs:
  use `docker logs <container>` to catch request-handler exceptions that Studio may only summarize.
- Generated example files:
  check `specs/*_examples/` for artifacts created by the `Examples` tab.

## Automation Hints

- Wait for the left tree to load before interacting with it.
- In the tree, target the expander icon for folders and the title text for files.
- For OpenAPI example generation, wait for the iframe content to load before interacting with the iframe content rather than the top-level page.
- After switching to `Mock`, wait for the tab to initialize before filling `#mockPort` or clicking the run button.
- After switching to `Test`, wait for the tab to initialize before filling `#testBaseUrl` or clicking the run button.
