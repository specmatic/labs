# 429 Too Many Requests

Implement the trigger established by the contract and requirements: for example, caller limiting, protective load
shedding, an open circuit, dependency response translation, or explicitly required dependency unavailability.
Requirements outrank conventional semantics; when they are silent, dependency unavailability normally maps to `503`,
while `429` denotes throttling.

Return `Retry-After` from the real limiting, circuit, or recovery state. A limiter or open circuit must not make another
downstream call until retry is permitted.

Verify the complete interaction: the application returns `429`, Specmatic uses `Retry-After` to retry the original
operation, the transient dependency expectation is exhausted, normal downstream behavior is reached, and the final
response matches a declared SUT success. Checking only the initial `429` is insufficient.

If Specmatic does not generate the required case, add a contract-valid external example. Correlate it to the downstream
expectation through an existing, forwarded contract value that ordinary success examples cannot select. Do not invent a
test-only header, query parameter, or body field.
