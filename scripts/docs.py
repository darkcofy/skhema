#!/usr/bin/env python3
"""Generate a self-contained HTML architecture handbook for a client.

Usage:
    python scripts/docs.py --client demo
    python scripts/docs.py --client demo --title "NovaPay"
    python scripts/docs.py --client demo --output novapay-v2.html
"""
import argparse
import html as html_mod
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.gallery import (
    discover_diagrams,
    group_by_type,
    diagram_name,
    parse_client_yaml,
    TYPE_ORDER,
    TYPE_LABELS,
)


def parse_markdown(md: str) -> str:
    """Convert markdown text to HTML. Single-pass, no nested inline formatting."""
    if not md or not md.strip():
        return ""

    lines = md.split("\n")
    result = []
    i = 0

    def inline(text):
        text = html_mod.escape(text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(html_mod.escape(lines[i]))
                i += 1
            i += 1
            code = "\n".join(code_lines)
            result.append(f"<pre><code>{code}</code></pre>")
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m:
            level = len(m.group(1))
            text = inline(m.group(2))
            result.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        # Table
        if "|" in stripped and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1].strip()):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i].strip():
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            header_html = "".join(f"<th>{inline(h)}</th>" for h in headers)
            rows_html = ""
            for row in rows:
                cells_html = "".join(f"<td>{inline(c)}</td>" for c in row)
                rows_html += f"<tr>{cells_html}</tr>"
            result.append(f"<table><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                bq_lines.append(inline(lines[i].strip()[2:]))
                i += 1
            result.append(f"<blockquote><p>{'<br>'.join(bq_lines)}</p></blockquote>")
            continue

        # Bullet list
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline(lines[i].strip()[2:])}</li>")
                i += 1
            result.append(f"<ul>{''.join(items)}</ul>")
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                items.append(f"<li>{inline(text)}</li>")
                i += 1
            result.append(f"<ol>{''.join(items)}</ol>")
            continue

        # Paragraph
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#") and not lines[i].strip().startswith("```") and not lines[i].strip().startswith("> ") and not lines[i].strip().startswith("- ") and not re.match(r'^\d+\.\s', lines[i].strip()):
            para_lines.append(inline(lines[i].strip()))
            i += 1
        if para_lines:
            result.append(f"<p>{' '.join(para_lines)}</p>")

    return "\n".join(result)
