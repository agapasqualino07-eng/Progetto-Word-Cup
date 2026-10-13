"""Renderizza i template con preview/sample-data.json in preview/*.html,
aggiungendo una fascia ben visibile "ANTEPRIMA — DATI DI ESEMPIO".
Uso (da site/): python3 tools/build_preview.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render  # noqa: E402

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNER = ('<div style="background:#92400E;color:#fff;text-align:center;font:700 14px/1.4 system-ui,sans-serif;'
          'padding:6px 12px">ANTEPRIMA — tutti i contenuti sono DATI DI ESEMPIO, non reali</div>')

for name in ("product.html", "index.html"):
    with open(os.path.join(SITE, "preview", "sample-data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(SITE, "template", name), encoding="utf-8") as f:
        out = render(f.read(), data)
    out = out.replace("<body>", "<body>\n" + BANNER, 1)
    dst = os.path.join(SITE, "preview", name)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print("scritto", dst)
