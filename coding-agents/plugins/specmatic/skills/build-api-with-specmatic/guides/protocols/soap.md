# SOAP / WSDL

Resolve service, port, binding, actions, input/output messages, namespaces, headers, faults, imported XSDs, and
endpoint. Generate native SOAP bindings/serialization. For dependencies, map actions, XML transforms, headers, and
faults; keep endpoint configurable.

## Configuration v3

```yaml
# provider test
wsdl:
  type: test
  baseUrl: "{SOAP_PROVIDER_URL:<provider-url>}"

# dependency mock
wsdl:
  type: mock
  host: "{SOAP_DEPENDENCY_HOST:<dependency-host>}"
  port: "{SOAP_DEPENDENCY_PORT:<dependency-port>}"
```

WSDL accepts `baseUrl`, or `host` plus `port`. When multiple WSDLs use different endpoints, assign stable specification
IDs and matching per-spec overrides under `wsdl.specs`.
