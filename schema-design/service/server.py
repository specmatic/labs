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

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return None

    def _missing(self, body, keys):
        return [key for key in keys if not body.get(key)]

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
        if self.path in ("/", "/health"):
            self._send_json(200, {"status": "ok"})
            return

        self._send_json(404, {"error": "Not Found", "path": self.path})

    def do_POST(self):
        if self.path != "/payments":
            self._send_json(404, {"error": "Not Found", "path": self.path})
            return

        body = self._read_json()
        if body is None:
            self._send_json(400, {"message": "Invalid JSON"})
            return

        payment_type = body.get("paymentType")

        if payment_type == "card":
            required = ["cardNumber", "cardExpiry", "cardCvv"]
            missing = self._missing(body, required)
            if missing:
                self._send_json(400, {"message": f"Missing card fields: {', '.join(missing)}"})
                return
        elif payment_type == "bank_transfer":
            required = ["bankAccountNumber", "bankRoutingNumber", "bankAccountHolder"]
            missing = self._missing(body, required)
            if missing:
                self._send_json(400, {"message": f"Missing bank transfer fields: {', '.join(missing)}"})
                return
        else:
            self._send_json(400, {"message": "paymentType must be card or bank_transfer"})
            return

        self._send_json(201, {"id": 1, "status": "accepted"})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
