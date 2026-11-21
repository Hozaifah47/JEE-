#!/usr/bin/env python3
"""Serve the static portal with the local cluster-refresh endpoint."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("PORT", "3000"))


class PortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path != "/api/refresh-clusters":
            self.send_error(404, "Unknown API route")
            return
        script = ROOT / "07_SCRIPTS" / "generate_all_cluster_pages.py"
        if os.environ.get("DRY_RUN") != "1":
            try:
                subprocess.Popen(
                    ["python3", str(script)],
                    cwd=str(ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as exc:
                self.send_error(500, f"Could not start cluster refresh: {exc}")
                return
        payload = json.dumps({"status": "started"}).encode()
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    print(f"Serving {ROOT} on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), PortalHandler).serve_forever()
