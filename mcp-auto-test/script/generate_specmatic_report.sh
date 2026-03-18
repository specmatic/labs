#!/bin/bash
# generate_specmatic_report.sh
# Convert Specmatic JSON test results into a formatted HTML report.
# Requires: mcp_test_report.json and tools_schema.json in the same directory.

REPORT_DIR="build/reports/specmatic/mcp"
INPUT="$REPORT_DIR/mcp_test_report.json"
SCHEMA="$REPORT_DIR/tools_schema.json"
OUTPUT="$REPORT_DIR/specmatic_report.html"

if [ ! -f "$INPUT" ]; then
  echo "❌ File $INPUT not found in current directory."
  exit 1
fi

if [ ! -f "$SCHEMA" ]; then
  echo "❌ File $SCHEMA not found in current directory."
  exit 1
fi

case "$(uname -s)" in
  CYGWIN*|MINGW*|MSYS*|MINGW32*|MINGW64*)
    PYTHON_CMD="python"
    ;;
  *)
    PYTHON_CMD="python3"
    ;;
esac

/usr/bin/env $PYTHON_CMD <<'PYCODE'
import json, html, datetime, os, webbrowser

INPUT = "build/reports/specmatic/mcp/mcp_test_report.json"
SCHEMA = "build/reports/specmatic/mcp/tools_schema.json"
OUTPUT = "build/reports/specmatic/mcp/specmatic_report.html"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)
with open(SCHEMA, "r", encoding="utf-8") as f:
    tools = {t["name"]: t for t in json.load(f)}

total = len(data)
passed = sum(1 for t in data if t.get("verdict") == "PASSED")
failed = sum(1 for t in data if t.get("verdict") == "FAILED")
negatives = sum(1 for t in data if t.get("negative") is True)
positives = total - negatives

def esc(s): return html.escape(str(s) if s is not None else "")
def pretty(obj):
    try: return json.dumps(obj, indent=2, ensure_ascii=False)
    except: return str(obj)

rows_html = []
for i, t in enumerate(data, start=1):
    tool = t.get("toolName", "")
    verdict = t.get("verdict", "")
    negative = t.get("negative") is True
    badge_class = "badge-pass" if verdict == "PASSED" else "badge-fail" if verdict == "FAILED" else "badge-other"
    verdict = "✅" if verdict == "PASSED" else "❌" if verdict == "FAILED" else "➖"
    error_html = f"<pre>{esc(t.get('error'))}</pre>" if t.get("error") else "<em>—</em>"
    req, resp = pretty(t.get("request", {})), pretty(t.get("response", {}))

    # schema lookup
    tool_schema = tools.get(tool, {})
    input_schema = pretty(tool_schema.get("inputSchema")) if tool_schema.get("inputSchema") else "—"
    output_schema = pretty(tool_schema.get("outputSchema")) if tool_schema.get("outputSchema") else "—"

    detail_id = f"detail-{i}"
    rows_html.append(f"""
    <tr class="{'neg-true' if negative else 'neg-false'}">
      <td>{i}</td>
      <td>{esc(t.get("name",""))}</td>
      <td>{esc(tool)}</td>
      <td><span class="badge {badge_class}">{verdict}</span></td>
      <td>{error_html}</td>
      <td><button onclick="toggleRow('{detail_id}')">View</button></td>
    </tr>
    <tr id="{detail_id}" class="detail-row">
      <td colspan="7">
        <div class="grid-req">
          <div>
            <h4>Request</h4>
            <pre>{esc(req)}</pre>
          </div>
          <div>
            <h4>Input Schema</h4>
            <pre>{esc(input_schema)}</pre>
          </div>
        </div>
        <div class="grid-res">
          <div>
            <h4>Response</h4>
            <pre>{esc(resp)}</pre>
          </div>
          <div>
            <h4>Output Schema</h4>
            <pre>{esc(output_schema)}</pre>
          </div>
        </div>
      </td>
    </tr>
    """)

rows_html = "\n".join(rows_html)
generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>Specmatic MCP Auto-Test Report</title>
<style>
body {{ font-family: -apple-system, Segoe UI, sans-serif; background:#0b0e14; color:#e6e6e6; font-size: 16px; line-height: 1.5;}}
table {{ border-collapse: collapse; width:100%; }}
th, td {{ border:1px solid #2b313b; padding:8px; vertical-align: top; font-size: 16px; }}
th {{ background:#11151c; position:sticky; top:0; }}
.badge-pass {{ color:#20c997; }}
.badge-fail {{ color:#ff6b6b; }}
.detail-row {{ display:none; background:#0c111a; }}
pre {{ background:#0f1320; padding:8px; border-radius:6px; overflow-x:auto; white-space: pre-wrap; word-wrap: break-word; font-size: 16px; }}
button {{ background:#1a1f29; color:#e6e6e6; border:1px solid #2b313b; padding:4px 8px; border-radius:6px; cursor:pointer; }}
.grid-req {{ display:grid; grid-template-columns:30% 70%; gap:16px; margin-bottom:16px; }}
.grid-res {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
</style>
<script>
function toggleRow(id) {{
  const row = document.getElementById(id);
  row.style.display = (row.style.display === "table-row") ? "none" : "table-row";
}}
</script>
</head>
<body>
<h1>Specmatic MCP Auto-Test Report</h1>
<p>Generated {generated_at}</p>
<p>Total: {total} | Passed: {passed} | Failed: {failed} | Positives: {positives} | Negatives: {negatives}</p>
<table>
<tr><th>#</th><th>Test Scenario Name</th><th>Tool</th><th>Verdict</th><th>Error</th><th>Details</th></tr>
{rows_html}
</table>
</body></html>
"""

with open(OUTPUT,"w",encoding="utf-8") as f:
    f.write(html_doc)

print(f"✅ Report written to {OUTPUT}")
abs_path = os.path.abspath(OUTPUT)
if os.environ.get("SPECMATIC_OPEN_REPORT", "").lower() in {"1", "true", "yes"}:
    webbrowser.open("file://" + abs_path)
    print("🌐 Opening report in browser...")
else:
    print(f"📄 Report available at {abs_path}")
PYCODE
