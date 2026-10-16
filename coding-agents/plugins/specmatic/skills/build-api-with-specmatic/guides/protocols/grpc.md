# gRPC / Protobuf

Resolve package/service/full methods, unary/streaming type, messages, metadata, statuses, imports, code-generation
target, and timeout. Generate framework-native server/client stubs and keep endpoints, import paths, and timeouts
configurable. For dependencies, map methods, message transformations, metadata, errors, and streaming behavior rather
than assuming services match.

## Configuration v3

```yaml
# provider test
protobuf:
  type: test
  host: "{GRPC_PROVIDER_HOST:<provider-host>}"
  port: "{GRPC_PROVIDER_PORT:<provider-port>}"
  requestTimeout: 5000

# dependency mock
protobuf:
  type: mock
  host: "{GRPC_DEPENDENCY_HOST:<dependency-host>}"
  port: "{GRPC_DEPENDENCY_PORT:<dependency-port>}"
```

`requestTimeout` is milliseconds. Add `importPaths` only when imports require additional roots and `protocVersion` only
when compatibility requires a pin.
