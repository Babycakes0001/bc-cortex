#!/usr/bin/env python3
"""
BC🖤CORTEX — indexer.

Scans a folder of Markdown notes, finds the links between them, and bakes a
self-contained bc-cortex.html (a neon 3D star-map of your notes) from template.html.

ZERO network, zero AI calls — pure local filesystem scan.

Where it looks:
  - $BC_CORTEX_ROOT if set, otherwise ./brain
Put your own .md files in there (subfolders become color groups). A folder named
'private' is never drawn on the map — it stays sealed until you unlock it in the
viewer with your passphrase (see set-private-key.sh).

Usage:  python3 index.py
Output: brain.json + bc-cortex.html
"""
import json
import math
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get("BC_CORTEX_ROOT", os.path.join(HERE, "brain")))

PALETTE = ["#ffd24a", "#1f8fff", "#ff4da6", "#00e5ff", "#5cf08a", "#ff5e5e",
           "#ffab40", "#e8e8ff", "#fff176", "#8f7bff", "#ff9f1c", "#2ec4b6",
           "#e71d36", "#7bdff2", "#c792ea", "#a0e426"]
FALLBACK_COLOR = "#8f7bff"

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
BAREFILE_RE = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9_-]{4,})\.md\b")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FM_FIELD_RE = re.compile(r"^(name|title|description|desc):\s*(.+)$", re.MULTILINE)


def group_of(rel):
    parts = rel.split("/")
    return parts[0] if len(parts) > 1 else "notes"


def main():
    if not os.path.isdir(ROOT):
        print(f"no notes folder at {ROOT} — create it and drop .md files in, "
              f"or set BC_CORTEX_ROOT.")
        return 1

    files = []
    for root, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() != "private"]
        for n in sorted(names):
            if n.endswith(".md"):
                files.append(os.path.relpath(os.path.join(root, n), ROOT).replace(os.sep, "/"))

    nodes, by_stem, by_rel = [], {}, {}
    for rel in files:
        try:
            text = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        fm = {}
        m = FRONTMATTER_RE.match(text)
        if m:
            fm = {k: v.strip().strip('"') for k, v in FM_FIELD_RE.findall(m.group(1))}
        stem = os.path.splitext(os.path.basename(rel))[0]
        node = {
            "id": rel,
            "label": fm.get("name") or fm.get("title") or stem,
            "desc": (fm.get("description") or fm.get("desc") or "")[:200],
            "group": group_of(rel),
            "val": max(1.5, math.sqrt(len(text)) / 14),
            "size": len(text),
            "mtime": datetime.fromtimestamp(os.path.getmtime(os.path.join(ROOT, rel))).strftime("%Y-%m-%d"),
            "_text": text,
        }
        nodes.append(node)
        by_rel[rel] = node
        by_stem.setdefault(stem.lower(), node)

    # edges: [[wiki-links]] and bare filename.md mentions, resolved by file stem
    edges = {}
    def add_edge(a, b):
        if a == b:
            return
        key = (a, b) if a < b else (b, a)
        edges[key] = edges.get(key, 0) + 1
    for node in nodes:
        text, src = node.pop("_text"), node["id"]
        for ref in WIKILINK_RE.findall(text):
            t = by_stem.get(ref.strip().lower())
            if t:
                add_edge(src, t["id"])
        for ref in BAREFILE_RE.findall(text):
            t = by_stem.get(ref.lower())
            if t:
                add_edge(src, t["id"])

    links = [{"source": a, "target": b, "w": w} for (a, b), w in edges.items()]
    graph = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "nodes": nodes, "links": links}

    groups = sorted({n["group"] for n in nodes})
    colors = {g: PALETTE[i % len(PALETTE)] for i, g in enumerate(groups)}
    colors.setdefault("memory", FALLBACK_COLOR)
    colors["dust"] = "rgba(215,218,235,0.4)"
    labels = {g: g for g in groups}

    template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    html = (template
            .replace("__GRAPH_DATA__", json.dumps(graph))
            .replace("__VIEW_ONLY__", "false")
            .replace("__COLORS__", json.dumps(colors))
            .replace("__LABELS__", json.dumps(labels)))
    open(os.path.join(HERE, "brain.json"), "w", encoding="utf-8").write(json.dumps(graph))
    open(os.path.join(HERE, "bc-cortex.html"), "w", encoding="utf-8").write(html)

    linked = {n for pair in edges for n in pair}
    print(f"BC Cortex indexed: {len(nodes)} stars, {len(links)} links, "
          f"{len(nodes) - len(linked)} lone stars, {len(groups)} groups -> bc-cortex.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
