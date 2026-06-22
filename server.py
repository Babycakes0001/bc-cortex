#!/usr/bin/env python3
"""
BC🖤CORTEX — local read-only server.

Serves the star-map and your note files to your own browser, on 127.0.0.1 only.
Never touches the internet, never writes to disk.

  /               -> bc-cortex.html
  /file/<relpath> -> raw text of one .md note (the reader panel)
  /search?q=...   -> full-content grep across your notes (multi-word = AND)

Privacy: a folder named 'private' is refused by default. It unlocks only when the
browser sends the right passphrase (set one with set-private-key.sh) — verified
here against a salted hash; the passphrase itself is never stored.
"""
import hashlib
import http.server
import json
import os
import subprocess
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get("BC_CORTEX_ROOT", os.path.join(HERE, "brain")))
CORTEX_HTML = os.path.join(HERE, "bc-cortex.html")
KEYFILE = os.path.join(HERE, ".private-key")
PORT = int(os.environ.get("BC_CORTEX_PORT", "9091"))


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authed(self):
        key = self.headers.get("X-Cortex-Key", "")
        if not key:
            return False
        try:
            with open(KEYFILE) as f:
                salt, want = f.read().strip().split(":", 1)
            return hashlib.sha256((salt + key).encode("utf-8")).hexdigest() == want
        except Exception:
            return False

    def _safe(self, rel, authed):
        # resolve rel under ROOT; refuse traversal, dotfiles, and private-unless-unlocked
        if not rel.endswith(".md") or rel.startswith("/"):
            return None
        full = os.path.realpath(os.path.join(ROOT, rel))
        if not (full == ROOT or full.startswith(ROOT + os.sep)):
            return None
        low = os.path.relpath(full, ROOT).replace(os.sep, "/").lower()
        if any(seg.startswith(".") for seg in low.split("/")):
            return None
        if "private" in low and not authed:
            return None
        return full

    def _all_md(self, authed):
        out = []
        for root, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and (authed or d.lower() != "private")]
            for n in names:
                if n.endswith(".md"):
                    out.append(os.path.relpath(os.path.join(root, n), ROOT).replace(os.sep, "/"))
        return out

    def _search(self, q, authed):
        words = [w for w in q.lower().split() if len(w) >= 2]
        if not words:
            return json.dumps({"q": q, "authed": authed, "count": 0, "hits": []})
        allmd = self._all_md(authed)
        nameset = set(allmd)
        result = None
        for w in words:
            try:
                out = subprocess.run(["grep", "-rilF", "--include=*.md", "-e", w, "--", "."],
                                     cwd=ROOT, capture_output=True, text=True, timeout=25).stdout
            except Exception:
                out = ""
            wset = {ln.strip().lstrip("./").replace("\\", "/") for ln in out.splitlines() if ln.strip()}
            wset |= {rel for rel in nameset if w in rel.lower()}
            result = wset if result is None else (result & wset)
            if not result:
                break
        hits = sorted(r for r in (result or set())
                      if r in nameset and (authed or "private" not in r.lower()))
        return json.dumps({"q": q, "authed": authed, "count": len(hits), "hits": hits[:1500]})

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?", 1)[0])
        if path in ("/", "/cortex", "/index.html"):
            try:
                return self._send(200, open(CORTEX_HTML, "rb").read(), "text/html; charset=utf-8")
            except OSError:
                return self._send(503, "not built yet — run: python3 index.py")
        if path == "/search":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("q", [""])[0].strip()
            if len(q) < 2:
                return self._send(200, '{"q":"","authed":false,"count":0,"hits":[]}', "application/json")
            return self._send(200, self._search(q, self._authed()), "application/json")
        if path.startswith("/file/"):
            full = self._safe(path[len("/file/"):], self._authed())
            if not full:
                return self._send(403, "refused")
            try:
                return self._send(200, open(full, encoding="utf-8", errors="replace").read())
            except OSError:
                return self._send(404, "not found")
        return self._send(404, "not found")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"BC Cortex serving {ROOT} at http://127.0.0.1:{PORT}  (Ctrl-C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
