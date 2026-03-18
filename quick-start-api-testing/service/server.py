import json
import random
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


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

    def do_HEAD(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/verifyUser":
            self._send_json(404, {"error": "Not Found", "path": self.path})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        chooser = random.Random(int(payload["userId"]))

        response = {
            "handledBy": "verification-service",
            "decision": chooser.choice(["approved", "verified"]),
            "referenceCode": f"VRF-{chooser.randint(100000, 999999)}",
            "processedOn": datetime.now(timezone.utc).date().isoformat()
        }
        self._send_json(200, response)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
