#!/usr/bin/env python3
"""
Generations Covered – REST API Server
Pure Python standard library (no external dependencies).

Ready for deployment on Render, Railway, Fly.io, etc.

Run locally:
    python -m api.server

Environment variables:
    PORT          – port to listen on (default 8000)
    HOST          – bind address (default 0.0.0.0)
"""

from __future__ import annotations

import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from typing import Any

from .hospital_service import get_service


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: Any):
    body = json.dumps(payload, indent=2, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    # CORS – allow any frontend origin
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.command}] {self.path} -> {args[1] if len(args) > 1 else ''}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            svc = get_service()

            if path == "/health" or path == "/":
                return json_response(self, 200, {
                    "status": "ok",
                    "service": "Generations Covered API",
                    "version": "1.0"
                })

            if path == "/api/v1/fpl":
                return json_response(self, 200, svc.get_fpl_table())

            if path == "/api/v1/hospitals":
                return json_response(self, 200, {"hospitals": svc.list_hospitals()})

            if path.startswith("/api/v1/hospitals/"):
                parts = path.split("/")
                # /api/v1/hospitals/{id}
                # /api/v1/hospitals/{id}/documents
                # /api/v1/hospitals/{id}/form-mapping
                if len(parts) == 5:
                    hospital_id = parts[4]
                    hospital = svc.get_hospital(hospital_id)
                    if not hospital:
                        return json_response(self, 404, {"error": "Hospital not found"})
                    return json_response(self, 200, hospital)
                if len(parts) == 6 and parts[5] == "documents":
                    hospital_id = parts[4]
                    docs = svc.get_required_documents(hospital_id)
                    if not docs:
                        return json_response(self, 404, {"error": "Documents not found for hospital"})
                    return json_response(self, 200, docs)
                if len(parts) == 6 and parts[5] == "form-mapping":
                    hospital_id = parts[4]
                    mapping = svc.get_form_mapping(hospital_id)
                    if not mapping:
                        return json_response(self, 404, {"error": "Form mapping not found"})
                    return json_response(self, 200, mapping)

            if path == "/api/v1/personas":
                return json_response(self, 200, {"personas": svc.list_personas()})

            if path.startswith("/api/v1/personas/"):
                persona_id = path.split("/")[-1]
                persona = svc.get_persona(persona_id)
                if not persona:
                    return json_response(self, 404, {"error": "Persona not found"})
                return json_response(self, 200, persona)

            return json_response(self, 404, {"error": "Not found", "path": path})

        except Exception as e:
            traceback.print_exc()
            return json_response(self, 500, {"error": str(e)})

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            svc = get_service()

            if path == "/api/v1/eligibility":
                body = read_json_body(self)

                hospital_id = body.get("hospital_id")
                household_size = int(body.get("household_size", 1))
                annual_income = float(body.get("annual_income", 0))
                uninsured = bool(body.get("uninsured", True))
                georgia_resident = bool(body.get("georgia_resident", True))
                fulton_or_dekalb = bool(body.get("fulton_or_dekalb", False))
                bill_amount = float(body.get("bill_amount", 0))

                if not hospital_id:
                    return json_response(self, 400, {"error": "hospital_id is required"})

                result = svc.check_eligibility(
                    hospital_id=hospital_id,
                    household_size=household_size,
                    annual_income=annual_income,
                    uninsured=uninsured,
                    georgia_resident=georgia_resident,
                    fulton_or_dekalb=fulton_or_dekalb,
                    bill_amount=bill_amount,
                )
                return json_response(self, 200, result)

            return json_response(self, 404, {"error": "Not found", "path": path})

        except Exception as e:
            traceback.print_exc()
            return json_response(self, 500, {"error": str(e)})


def main():
    print(f"Starting Generations Covered API on http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /health")
    print("  GET  /api/v1/fpl")
    print("  GET  /api/v1/hospitals")
    print("  GET  /api/v1/hospitals/{id}")
    print("  GET  /api/v1/hospitals/{id}/documents")
    print("  GET  /api/v1/hospitals/{id}/form-mapping")
    print("  POST /api/v1/eligibility")
    print("  GET  /api/v1/personas")
    print("  GET  /api/v1/personas/{id}")
    print()

    server = ThreadingHTTPServer((HOST, PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
        server.shutdown()


if __name__ == "__main__":
    main()
