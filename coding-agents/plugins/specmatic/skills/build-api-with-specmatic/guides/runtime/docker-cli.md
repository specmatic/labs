# Docker CLI

Use the `specmatic/enterprise` image tag specified by the project or environment. If none is specified, use `specmatic/enterprise:latest`. Commands are the same as [CLI](cli.md), with the container entrypoint replacing `java -jar`.

## Mounts and execution

Run from the application project root—the directory containing `specmatic.yaml`. Mount that directory at `/workspace` and set the container working directory to `/workspace`. This preserves relative paths to contracts, examples and other project files. Mount any referenced files outside the project separately at paths reachable from the container configuration.

Configure report output under `specmatic-reports/` and mount that directory writable. Replace the descriptive placeholders below with the image, addresses and ports chosen for this environment.

```bash
SPECMATIC_IMAGE="<selected-specmatic-enterprise-image>"
PROVIDER_URL="<provider-url-reachable-from-container>"
MOCK_PORT="<mock-port-in-specmatic.yaml>"
HOST_MOCK_PORT="<port-the-application-will-call>"

mkdir -p specmatic-reports

docker run --rm \
  --mount "type=bind,source=$PWD,target=/workspace,readonly" \
  --mount "type=bind,source=$PWD/specmatic-reports,target=/workspace/specmatic-reports" \
  --mount "type=bind,source=$HOME/.specmatic,target=/root/.specmatic,readonly" \
  --workdir /workspace \
  --env "PROVIDER_URL=$PROVIDER_URL" \
  --env "DEPENDENCY_HOST=0.0.0.0" \
  --env "DEPENDENCY_PORT=$MOCK_PORT" \
  --publish "$HOST_MOCK_PORT:$MOCK_PORT" \
  "$SPECMATIC_IMAGE" run-suite --agent
```

This example assumes `specmatic.yaml` uses `{PROVIDER_URL:...}`, `{DEPENDENCY_HOST:...}` and `{DEPENDENCY_PORT:...}`. Adapt the variable names to the actual configuration. For commands that modify `specmatic.yaml`, such as `config generate`, mount the project writable by omitting `readonly`.

## Networking

For an application running on the host:

- Configure its downstream URL to use the published host mock port.
- Configure the mock to bind to `0.0.0.0` inside the container.
- On Docker Desktop, use `host.docker.internal` in the provider URL to reach the host application. Container-local `localhost` refers to the container itself. On other Docker installations, use a supported host gateway or network configuration.

For sibling containers, use a shared container network and addresses reachable on that network. Publish each additional dependency port separately when its caller is outside the container network. Forward environment variables used by supplied fixture URL templates with `--env` so those fixtures reach the intended dependencies; see [dependency mocking](../dependency-mocking.md).

## Licensing and results

The license mount assumes an existing `$HOME/.specmatic` directory. Alternatively, forward existing `SPECMATIC_LICENSE_CONTENT` with `--env SPECMATIC_LICENSE_CONTENT`; for `SPECMATIC_LICENSE_PATH`, mount the referenced file and set the variable to its container path. Keep license contents out of source, images, logs and reports.

Inspect the suite's exit status, output and persisted reports, and propagate failures. `--rm` removes the container after it exits. Stop application processes you started when finished.
