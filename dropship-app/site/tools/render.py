"""Renderer Mustache minimale (solo standard library) per i template dello store.

Supporta: {{var}} (escape HTML), {{{var}}} (HTML grezzo, va sanificato a monte),
{{#sec}}...{{/sec}} (bool / lista / oggetto), {{^sec}}...{{/sec}} (inverso),
{{.}} (elemento corrente), nomi puntati (hero_image.src).

Uso:
    python3 tools/render.py template/product.html preview/sample-data.json preview/product.html

Il generatore aggiunge in automatico, per ogni elemento di `images`:
`loading`/`fetchpriority` (eager+high sulla prima, lazy+auto sulle altre) e `last`.
"""
import html
import json
import re
import sys

TAG = re.compile(r"\{\{(\{|#|\^|/)?\s*([\w.]+)\s*\}?\}\}")


def _lookup(stack, name):
    if name == ".":
        return stack[-1]
    head, *rest = name.split(".")
    for ctx in reversed(stack):
        if isinstance(ctx, dict) and head in ctx:
            val = ctx[head]
            for part in rest:
                val = val.get(part) if isinstance(val, dict) else None
            return val
    return None


def _parse(tpl, pos=0, closing=None):
    nodes = []
    while True:
        m = TAG.search(tpl, pos)
        if not m:
            if closing:
                raise ValueError(f"sezione non chiusa: {closing}")
            nodes.append(("text", tpl[pos:]))
            return nodes, len(tpl)
        nodes.append(("text", tpl[pos:m.start()]))
        kind, name = m.group(1), m.group(2)
        pos = m.end()
        if kind in ("#", "^"):
            children, pos = _parse(tpl, pos, name)
            nodes.append((kind, name, children))
        elif kind == "/":
            if name != closing:
                raise ValueError(f"chiusura inattesa {name}, attesa {closing}")
            return nodes, pos
        elif kind == "{":
            nodes.append(("raw", name))
        else:
            nodes.append(("var", name))


def _render(nodes, stack):
    out = []
    for node in nodes:
        t = node[0]
        if t == "text":
            out.append(node[1])
        elif t in ("var", "raw"):
            val = _lookup(stack, node[1])
            s = "" if val is None or val is False else str(val)
            out.append(s if t == "raw" else html.escape(s, quote=True))
        elif t == "#":
            val = _lookup(stack, node[1])
            if isinstance(val, list):
                for item in val:
                    out.append(_render(node[2], stack + [item]))
            elif val:
                out.append(_render(node[2], stack + [val] if isinstance(val, dict) else stack))
        elif t == "^":
            val = _lookup(stack, node[1])
            if not val:
                out.append(_render(node[2], stack))
    return "".join(out)


def prepare(data):
    imgs = data.get("images") or []
    for i, img in enumerate(imgs):
        img.setdefault("loading", "eager" if i == 0 else "lazy")
        img.setdefault("fetchpriority", "high" if i == 0 else "auto")
        img["last"] = i == len(imgs) - 1
    # regola di onestà: niente blocco recensioni senza recensioni reali
    data["has_reviews"] = bool(data.get("reviews"))
    if not data["has_reviews"]:
        data["reviews_avg"] = data["reviews_count"] = None
    return data


def render(template_text, data):
    nodes, _ = _parse(template_text)
    return _render(nodes, [prepare(data)])


if __name__ == "__main__":
    src, data_path, dst = sys.argv[1:4]
    with open(src, encoding="utf-8") as f:
        tpl = f.read()
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(render(tpl, data))
    print(f"scritto {dst}")
