import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer


USER_PATH_PATTERN = re.compile(r"^/api/v1/users/(\d+)$")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return

    def _is_ready_path(self):
        return self.path in ("/", "/health")

    def do_HEAD(self):
        if self._is_ready_path():
            self.send_response(200)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self._is_ready_path():
            self._send_json(200, {"status": "ok"})
            return

        match = USER_PATH_PATTERN.fullmatch(self.path)
        if match:
            user_id = int(match.group(1))
            self._send_json(200, {"id": user_id, "name": "Jane Doe"})
            return

        self._send_json(404, {"error": "Not Found", "path": self.path})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
