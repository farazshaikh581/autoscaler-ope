# api-service: the second application of the OPE study.
#
# A JSON API with a downstream call. Each GET / request
#   1. builds a result set of N records, N log-normal (median API_RECORDS, sigma
#      API_SIGMA, capped at API_MAX_RECORDS), then serialises, parses, sorts and hashes
#      it: CPU work with a heavy-tailed size, unlike web-service's fixed hash loop;
#   2. waits for a downstream call (a cache or database round trip), exponential with
#      mean API_WAIT_MS: latency the pod's CPU does not see.
# So the latency-load curve differs from web-service in both the service-time variance
# and a CPU-free latency component. Only the Python standard library is used.
import hashlib, http.server, json, math, os, random, socketserver, time

RECORDS = float(os.environ.get("API_RECORDS", "40"))
SIGMA = float(os.environ.get("API_SIGMA", "0.9"))
MAX_RECORDS = int(os.environ.get("API_MAX_RECORDS", "2000"))
WAIT_MS = float(os.environ.get("API_WAIT_MS", "3"))
MU = math.log(RECORDS)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok"); return
        t0 = time.monotonic()
        rng = random.Random()
        n = min(MAX_RECORDS, max(1, int(rng.lognormvariate(MU, SIGMA))))
        rows = [{"id": rng.getrandbits(32), "score": rng.random(), "name": "item-%d" % i,
                 "tags": [rng.getrandbits(8) for _ in range(4)]} for i in range(n)]
        rows = json.loads(json.dumps(rows))
        rows.sort(key=lambda r: (r["score"], r["id"]))
        digest = hashlib.sha256(json.dumps(rows[:10]).encode()).hexdigest()[:16]
        cpu_ms = (time.monotonic() - t0) * 1000
        time.sleep(rng.expovariate(1.0 / WAIT_MS) / 1000.0 if WAIT_MS > 0 else 0.0)
        body = json.dumps({"status": "ok", "records": n, "digest": digest, "cpu_ms": round(cpu_ms, 2)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


socketserver.ThreadingTCPServer.daemon_threads = True
socketserver.ThreadingTCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("", 8080), Handler) as s:
    s.serve_forever()
