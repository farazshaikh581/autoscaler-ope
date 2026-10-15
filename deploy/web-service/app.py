import hashlib, os, time, json, http.server, socketserver
from urllib.parse import urlparse, parse_qs

WORK_ITERATIONS = int(os.environ.get("WORK_ITERATIONS", "250"))

# Resident memory ballast: GET /alloc?mb=N holds N MiB of touched pages so the
# pod's RSS reflects a memory-bound working set (the CPU-burn path allocates
# nothing). The RealClusterBackend drives this from the memory-bound trace, so
# the memory axis has real ground truth: if the ballast exceeds the container's
# memory limit the kernel OOM-kills it, exactly the pressure the policy must
# avoid by raising the memory request. GRAN pages are touched to force real
# pages resident under demand paging.
_ballast = bytearray()

def _set_ballast(mb):
    global _ballast
    n = max(0, int(mb)) * 1024 * 1024
    _ballast = bytearray()          # release the old buffer before allocating
    b = bytearray(n)
    for i in range(0, n, 4096):     # touch every page so RSS reflects the size
        b[i] = 1
    _ballast = b
    return n // (1024 * 1024)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok"); return
        if p.path == "/alloc":
            mb = _set_ballast(parse_qs(p.query).get("mb", ["0"])[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ballast_mb": mb}).encode()); return
        t0 = time.monotonic()
        data = b"x" * 1024
        for _ in range(WORK_ITERATIONS):
            data = hashlib.sha256(data).digest()
        elapsed_ms = (time.monotonic() - t0) * 1000
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "work_ms": round(elapsed_ms, 1)}).encode())
    def log_message(self, fmt, *args):
        pass

with socketserver.ThreadingTCPServer(("", 8080), Handler) as s:
    s.serve_forever()
