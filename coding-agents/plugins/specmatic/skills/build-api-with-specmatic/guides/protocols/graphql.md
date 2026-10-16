# GraphQL

Resolve schema entrypoints, fields, arguments, nullability, scalars/enums/input/object types, selection sets, variables,
examples, and headers/security. Generate native resolvers/client operations. For dependency calls, map
fields/variables/results/errors rather than assuming schemas match.

## Configuration v3

```yaml
# provider test
graphqlsdl:
  type: test
  host: "{GRAPHQL_PROVIDER_HOST:<provider-host>}"
  port: "{GRAPHQL_PROVIDER_PORT:<provider-port>}"

# dependency mock
graphqlsdl:
  type: mock
  host: "{GRAPHQL_DEPENDENCY_HOST:<dependency-host>}"
  port: "{GRAPHQL_DEPENDENCY_PORT:<dependency-port>}"
```

Host and port are optional when supplied by protocol defaults or invocation.
