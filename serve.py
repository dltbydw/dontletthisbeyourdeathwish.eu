#!/usr/bin/env -S uv run --locked --quiet
"""Local preview of the band site.

    ./serve.py               port 8000 of all interfaces (localhost and the LAN)
    ./serve.py --port 8080

Builds into _site/ like build.py, rebuilds on every save in content/, templates/
or static/ and reloads the browser. Changes to build.py or serve.py need a restart.
"""

import argparse
import sys
import threading
import time
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from build import CONTENT, SITE, STATIC, TEMPLATES, ContentError, build

# only in the served page, never in the file on disk: asks for /__version twice
# a second and reloads when the answer changes. Keeps asking while the server is
# down, so a restarted server picks the open tab up again.
RELOAD_SCRIPT = """<script>
  (async () => {
    let seen;
    for (;;) {
      try {
        const v = await (await fetch("/__version")).text();
        if (seen !== undefined && v !== seen) location.reload();
        seen = v;
      } catch {}
      await new Promise((r) => setTimeout(r, 500));
    }
  })();
</script>
"""


def snapshot(*directories):
    """Paths and modification times of all files below the directories."""
    files = []
    for directory in directories:
        for p in directory.rglob("*"):
            try:
                if p.is_file():
                    files.append((str(p), p.stat().st_mtime_ns))
            except FileNotFoundError:
                pass  # deleted between listing and stat, e.g. an editor's temp file
    return tuple(sorted(files))


def rebuild():
    """Like build, but an error only gets printed: the server keeps running and
    the browser keeps the last good page until the next save fixes it."""
    try:
        build()
    except ContentError as e:
        print(e, file=sys.stderr)
    except Exception:
        # template errors from Jinja; the traceback holds the template line
        traceback.print_exc()


def watch_sources():
    sources = (CONTENT, TEMPLATES, STATIC)
    seen = snapshot(*sources)
    while True:
        time.sleep(0.3)
        now = snapshot(*sources)
        if now != seen:
            seen = now
            print(time.strftime("%H:%M:%S"), "change in the sources")
            rebuild()


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE, **kwargs)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/__version":
            # changes whenever the site is rebuilt
            self.send_text(str(hash(snapshot(SITE))), "text/plain")
            return
        page = (SITE / (path.lstrip("/") or "index.html")).resolve()
        # pages get the reload script; .. in the path mustn't lead out of SITE
        if page.suffix == ".html" and page.is_relative_to(SITE) and page.is_file():
            html = page.read_text(encoding="utf-8")
            self.send_text(html.replace("</body>", RELOAD_SCRIPT + "</body>", 1),
                           "text/html")
        else:
            super().do_GET()

    def send_text(self, text, content_type):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # a replaced image shows up on reload instead of coming from the cache
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_request(self, code="-", size="-"):
        pass  # the polling would fill the terminal; errors still get logged


def serve(port):
    rebuild()
    threading.Thread(target=watch_sources, daemon=True).start()
    # all interfaces, so the phone on the same network can open it too
    server = ThreadingHTTPServer(("0.0.0.0", port), PreviewHandler)
    print(f"preview on http://localhost:{port} and port {port} of this machine's "
          "network address, Ctrl+C stops")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass



def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    serve(parser.parse_args().port)


if __name__ == "__main__":
    main()
