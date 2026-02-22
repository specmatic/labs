import json
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

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if self.path.startswith("/pets/"):
            pet_id = self.path.split("/")[-1]
            self._send_json(200, {
                "id": int(pet_id),
                "name": "Scooby",
                # Intentional mismatch for the exercise. This should be `type`.
                "petType": "Golden Retriever",
                "status": "Adopted"
            })
            return

        self._send_json(404, {"error": "Not Found", "path": self.path})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
