# README Generation

Write or update the application's README using the verified setup and acceptance workflow. Preserve accurate existing
user prose and omit inapplicable sections.

For a new README, use [the README template](../assets/templates/README.md.tmpl) as a starting point. Replace placeholders
with verified project facts and remove inapplicable sections.

Document only verified facts:

- immutable SUT and dependency contract sources;
- derived provider topology and mocked dependency boundaries;
- language, framework, protocol, Enterprise artifact/version, and invocation;
- prerequisites, non-secret environment variable names, and configurable endpoints;
- exact install, test, and build commands;
- schema-resiliency behavior, dependency verification, and report directory;
- important project files and observed limitations.

Explain license setup without a value or user-specific path using the shared [licensing guidance](specmatic-runtime.md#licensing).
Interactive host runs can use `specmatic get-license`; Docker-based runs forward existing license inputs or mount the
default `.specmatic` directory read-only; CI supplies a documented environment input. Describe `show-license` as a
debugging step when a licensing error occurs.

Do not claim unverified capabilities, mention public Specmatic runtimes, invent report paths, require Docker/CI when
unused, or add architecture imagery merely for presentation.
