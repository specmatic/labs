#!/bin/bash
set -u

specmatic mcp test \
  --url=http://mcp-server:8090/mcp \
  --transport-kind=STREAMABLE_HTTP \
  --dictionary-file=dictionary/orders.json \
  "$@"
test_status=$?

bash script/generate_specmatic_report.sh
report_status=$?

if [ $report_status -ne 0 ]; then
  exit $report_status
fi

exit $test_status
