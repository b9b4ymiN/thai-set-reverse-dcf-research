#!/usr/bin/env python3
"""Build a deployment-ready static documentation site for Netlify/GitHub Pages."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
NETLIFY = ROOT / "netlify"
SITE_URL_DEFAULT = "https://example.com"


NAV_LINKS = [
    ("Home", "index.html"),
    ("Thesis", "thesis.html"),
    ("Research", "research/index.html"),
    ("Backtest", "backtest/index.html"),
    ("About", "about/index.html"),
    ("Download", "download/index.html"),
]


STYLE_CSS = """
:root {
  --bg: #f4efe5;
  --bg-strong: #efe5d4;
  --paper: rgba(255, 251, 245, 0.9);
  --paper-strong: rgba(253, 248, 240, 0.97);
  --ink: #1f2427;
  --ink-soft: #445057;
  --muted: #6c7478;
  --line: rgba(40, 50, 58, 0.12);
  --accent: #b4562f;
  --accent-deep: #6a2f1b;
  --accent-soft: rgba(180, 86, 47, 0.12);
  --navy: #173144;
  --navy-soft: rgba(23, 49, 68, 0.08);
  --success: #20553a;
  --shadow: 0 22px 60px rgba(63, 47, 32, 0.14);
  --radius-lg: 28px;
  --radius-md: 18px;
  --radius-sm: 12px;
  --max-width: 1220px;
  --sidebar-width: 288px;
  --body-font: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
  --display-font: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(180, 86, 47, 0.16), transparent 34%),
    radial-gradient(circle at top right, rgba(23, 49, 68, 0.16), transparent 28%),
    linear-gradient(180deg, #f9f4ea 0%, #f4efe5 46%, #efe6d8 100%);
  font-family: var(--body-font);
  line-height: 1.68;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(95, 74, 54, 0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(95, 74, 54, 0.028) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.32), rgba(0, 0, 0, 0.08));
}

a {
  color: var(--accent-deep);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.15em;
}

a:hover {
  color: var(--accent);
}

img {
  max-width: 100%;
  display: block;
}

code,
pre {
  font-family: "SFMono-Regular", "Consolas", "Liberation Mono", monospace;
}

code {
  font-size: 0.92em;
  background: rgba(23, 49, 68, 0.08);
  padding: 0.15rem 0.38rem;
  border-radius: 0.45rem;
}

pre {
  overflow-x: auto;
  background: #142734;
  color: #f7efe5;
  padding: 1rem 1.15rem;
  border-radius: var(--radius-md);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.site-shell {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 28px 20px 60px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 22px;
  padding: 18px 22px;
  background: rgba(255, 251, 245, 0.74);
  border: 1px solid rgba(40, 50, 58, 0.08);
  border-radius: 999px;
  box-shadow: 0 12px 30px rgba(54, 40, 28, 0.08);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 12px;
  z-index: 20;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  text-decoration: none;
  color: inherit;
}

.brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background:
    linear-gradient(145deg, rgba(180, 86, 47, 0.94), rgba(23, 49, 68, 0.94));
  color: #fff7ef;
  display: grid;
  place-items: center;
  font-family: var(--display-font);
  font-size: 1.05rem;
  letter-spacing: 0.08em;
}

.brand-copy strong,
.hero-copy h1,
.page-intro h1,
.content-area h1,
.content-area h2,
.content-area h3,
.card h2,
.metric-card strong,
.toc-card h2 {
  font-family: var(--display-font);
}

.brand-copy strong {
  display: block;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.brand-copy span {
  display: block;
  color: var(--muted);
  font-size: 0.9rem;
}

.topbar nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
}

.topbar nav a {
  padding: 0.55rem 0.9rem;
  border-radius: 999px;
  text-decoration: none;
  font-size: 0.95rem;
  color: var(--ink-soft);
}

.topbar nav a.active,
.topbar nav a:hover {
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(290px, 0.95fr);
  gap: 22px;
  margin-bottom: 22px;
}

.hero-copy,
.hero-panel,
.card,
.content-wrap,
.toc-card,
.page-intro,
.site-footer {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
}

.hero-copy {
  padding: 30px 32px;
  position: relative;
  overflow: hidden;
}

.hero-copy::after {
  content: "";
  position: absolute;
  right: -48px;
  top: -58px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(180, 86, 47, 0.18), transparent 68%);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgba(180, 86, 47, 0.12);
  color: var(--accent-deep);
  font-size: 0.86rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h1,
.page-intro h1 {
  margin: 0.7rem 0 0.9rem;
  font-size: clamp(2.3rem, 4vw, 4rem);
  line-height: 1.02;
  letter-spacing: -0.03em;
}

.hero-copy p,
.page-intro p {
  margin: 0;
  max-width: 66ch;
  color: var(--ink-soft);
  font-size: 1.03rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  margin-top: 1.35rem;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.78rem 1.08rem;
  border-radius: 999px;
  border: 1px solid transparent;
  text-decoration: none;
  font-weight: 600;
}

.button.primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
  color: #fff9f2;
}

.button.secondary {
  background: rgba(255, 251, 245, 0.78);
  border-color: rgba(23, 49, 68, 0.15);
  color: var(--navy);
}

.hero-panel {
  padding: 24px;
  display: grid;
  gap: 12px;
  align-content: start;
}

.hero-panel h2 {
  margin: 0;
  color: var(--navy);
  font-size: 1.05rem;
  letter-spacing: 0.02em;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}

.metric-card {
  padding: 16px 18px;
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.62), rgba(255, 250, 244, 0.84));
  border: 1px solid rgba(40, 50, 58, 0.09);
}

.metric-card span {
  display: block;
  color: var(--muted);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.metric-card strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.85rem;
  line-height: 1.05;
}

.metric-card small {
  display: block;
  margin-top: 0.35rem;
  color: var(--ink-soft);
}

.panel-note {
  margin: 0;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 18px;
  margin-bottom: 22px;
}

.card {
  padding: 24px;
}

.card.span-4 {
  grid-column: span 4;
}

.card.span-6 {
  grid-column: span 6;
}

.card.span-8 {
  grid-column: span 8;
}

.card.span-12 {
  grid-column: span 12;
}

.card h2,
.card h3 {
  margin-top: 0;
  margin-bottom: 0.65rem;
  font-size: 1.4rem;
}

.kicker {
  margin: 0 0 0.7rem;
  color: var(--accent-deep);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.84rem;
}

.card p:last-child,
.card ul:last-child,
.card ol:last-child {
  margin-bottom: 0;
}

.list-clean {
  padding-left: 1.15rem;
  margin: 0.75rem 0 0;
}

.list-clean li + li {
  margin-top: 0.45rem;
}

.summary-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  font-size: 0.95rem;
}

.summary-table th,
.summary-table td {
  padding: 0.78rem 0.82rem;
  border-bottom: 1px solid rgba(40, 50, 58, 0.08);
  text-align: left;
  vertical-align: top;
}

.summary-table th {
  color: var(--navy);
  background: rgba(23, 49, 68, 0.06);
  font-weight: 700;
}

.figure-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.figure-card {
  padding: 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid rgba(40, 50, 58, 0.08);
}

.figure-card img {
  border-radius: var(--radius-sm);
  border: 1px solid rgba(40, 50, 58, 0.1);
}

.figure-card figcaption {
  margin-top: 0.8rem;
  color: var(--ink-soft);
  font-size: 0.93rem;
}

.content-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
  gap: 20px;
  align-items: start;
}

.content-wrap {
  padding: 28px 30px;
}

.toc-card {
  padding: 20px;
  position: sticky;
  top: 100px;
}

.toc-card h2 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-list li + li {
  margin-top: 0.36rem;
}

.toc-list a {
  display: block;
  padding: 0.32rem 0.45rem;
  border-radius: 0.6rem;
  text-decoration: none;
  color: var(--ink-soft);
}

.toc-list a:hover {
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
}

.toc-list .level-3 a {
  padding-left: 1rem;
  font-size: 0.93rem;
}

.page-intro {
  padding: 26px 30px;
  margin-bottom: 20px;
}

.content-area h1,
.content-area h2,
.content-area h3,
.content-area h4 {
  scroll-margin-top: 110px;
}

.content-area h1 {
  font-size: 2.35rem;
  line-height: 1.08;
}

.content-area h2 {
  font-size: 1.72rem;
  margin-top: 2.1rem;
}

.content-area h3 {
  font-size: 1.2rem;
  margin-top: 1.45rem;
}

.content-area p,
.content-area ul,
.content-area ol,
.content-area blockquote,
.content-area table {
  margin-top: 0.95rem;
  margin-bottom: 0.95rem;
}

.content-area ul,
.content-area ol {
  padding-left: 1.3rem;
}

.content-area li + li {
  margin-top: 0.38rem;
}

.content-area blockquote {
  padding: 1rem 1.1rem;
  border-left: 4px solid rgba(180, 86, 47, 0.45);
  background: rgba(180, 86, 47, 0.08);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.content-area table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: var(--radius-md);
  border: 1px solid rgba(40, 50, 58, 0.08);
}

.content-area th,
.content-area td {
  padding: 0.76rem 0.82rem;
  border-bottom: 1px solid rgba(40, 50, 58, 0.08);
  vertical-align: top;
}

.content-area th {
  background: rgba(23, 49, 68, 0.08);
  text-align: left;
}

.site-footer {
  margin-top: 24px;
  padding: 22px 24px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
}

.site-footer p {
  margin: 0;
  color: var(--ink-soft);
}

.footer-links {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1rem;
}

.pill {
  padding: 0.42rem 0.72rem;
  border-radius: 999px;
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
  font-size: 0.9rem;
}

.callout {
  padding: 16px 18px;
  border-radius: var(--radius-md);
  background: rgba(32, 85, 58, 0.08);
  border: 1px solid rgba(32, 85, 58, 0.18);
  color: var(--success);
}

.muted {
  color: var(--muted);
}

@media (max-width: 1060px) {
  .hero,
  .content-layout {
    grid-template-columns: 1fr;
  }

  .toc-card {
    position: static;
  }
}

@media (max-width: 860px) {
  .card-grid {
    grid-template-columns: 1fr;
  }

  .card.span-4,
  .card.span-6,
  .card.span-8,
  .card.span-12 {
    grid-column: auto;
  }

  .figure-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .site-shell {
    padding: 16px 14px 42px;
  }

  .topbar {
    border-radius: 26px;
    padding: 16px;
    position: static;
  }

  .topbar,
  .topbar nav {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-copy,
  .hero-panel,
  .card,
  .content-wrap,
  .page-intro {
    padding: 22px 20px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .hero-copy h1,
  .page-intro h1,
  .content-area h1 {
    font-size: clamp(2rem, 9vw, 2.7rem);
  }
}
""".strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def remap_href(href: str, link_map: dict[str, str]) -> str:
    normalized = href.strip()
    if normalized in link_map:
        return link_map[normalized]
    stripped = normalized.lstrip("./")
    if stripped in link_map:
        return link_map[stripped]
    try:
        relative = Path(normalized).resolve().relative_to(ROOT)
    except Exception:
        return href
    return link_map.get(relative.as_posix(), href)


def inline_markdown(text: str, link_map: dict[str, str] | None = None) -> str:
    placeholders: dict[str, str] = {}
    link_map = link_map or {}

    def stash(match: re.Match[str]) -> str:
        key = f"__CODE_{len(placeholders)}__"
        placeholders[key] = f"<code>{html.escape(match.group(1))}</code>"
        return key

    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", stash, escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{html.escape(remap_href(html.unescape(m.group(2)), link_map), quote=True)}">'
            f"{m.group(1)}</a>"
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for key, value in placeholders.items():
        escaped = escaped.replace(key, value)
    return escaped


def parse_table(
    lines: list[str],
    start: int,
    link_map: dict[str, str] | None = None,
) -> tuple[str, int] | None:
    if start + 1 >= len(lines):
        return None
    header = lines[start].strip()
    align = lines[start + 1].strip()
    if not header.startswith("|") or not header.endswith("|"):
        return None
    if not re.match(r"^\|(?:\s*:?-+:?\s*\|)+\s*$", align):
        return None

    rows: list[list[str]] = []
    cursor = start
    while cursor < len(lines):
        line = lines[cursor].strip()
        if not (line.startswith("|") and line.endswith("|")):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
        cursor += 1

    if len(rows) < 2:
        return None

    header_cells = rows[0]
    body_rows = rows[2:]
    parts = ["<table>", "<thead><tr>"]
    parts.extend(f"<th>{inline_markdown(cell, link_map)}</th>" for cell in header_cells)
    parts.append("</tr></thead><tbody>")
    for row in body_rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{inline_markdown(cell, link_map)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts), cursor


def markdown_to_html(
    markdown_text: str,
    toc_levels: Iterable[int] = (2, 3),
    link_map: dict[str, str] | None = None,
) -> tuple[str, list[dict[str, str | int]]]:
    lines = markdown_text.splitlines()
    output: list[str] = []
    toc: list[dict[str, str | int]] = []
    paragraph: list[str] = []
    list_buffer: list[str] = []
    list_type: str | None = None
    quote_buffer: list[str] = []
    code_buffer: list[str] = []
    code_lang = ""
    in_code = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            output.append(f"<p>{inline_markdown(text, link_map)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_buffer, list_type
        if list_buffer and list_type:
            tag = "ul" if list_type == "ul" else "ol"
            output.append(f"<{tag}>{''.join(list_buffer)}</{tag}>")
            list_buffer = []
            list_type = None

    def flush_quote() -> None:
        nonlocal quote_buffer
        if quote_buffer:
            joined = " ".join(item.strip() for item in quote_buffer if item.strip())
            output.append(f"<blockquote><p>{inline_markdown(joined, link_map)}</p></blockquote>")
            quote_buffer = []

    def flush_all() -> None:
        flush_paragraph()
        flush_list()
        flush_quote()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.rstrip()

        if in_code:
            if stripped.startswith("```"):
                classes = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                output.append(
                    f"<pre><code{classes}>{html.escape(chr(10).join(code_buffer))}</code></pre>"
                )
                code_buffer = []
                code_lang = ""
                in_code = False
            else:
                code_buffer.append(stripped)
            index += 1
            continue

        if stripped.startswith("```"):
            flush_all()
            in_code = True
            code_lang = stripped.removeprefix("```").strip()
            index += 1
            continue

        table_block = parse_table(lines, index, link_map)
        if table_block:
            flush_all()
            table_html, index = table_block
            output.append(table_html)
            continue

        if not stripped.strip():
            flush_all()
            index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_all()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            heading_id = slugify(heading_text)
            if level in toc_levels:
                toc.append({"level": level, "text": heading_text, "id": heading_id})
            output.append(
                f'<h{level} id="{heading_id}">{inline_markdown(heading_text, link_map)}</h{level}>'
            )
            index += 1
            continue

        blockquote_match = re.match(r"^>\s?(.*)$", stripped)
        if blockquote_match:
            flush_paragraph()
            flush_list()
            quote_buffer.append(blockquote_match.group(1))
            index += 1
            continue

        unordered_match = re.match(r"^\s*[-*]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\s*\d+\.\s+(.*)$", stripped)
        if unordered_match or ordered_match:
            flush_paragraph()
            flush_quote()
            next_type = "ul" if unordered_match else "ol"
            if list_type and list_type != next_type:
                flush_list()
            list_type = next_type
            item_text = unordered_match.group(1) if unordered_match else ordered_match.group(1)
            list_buffer.append(f"<li>{inline_markdown(item_text, link_map)}</li>")
            index += 1
            continue

        paragraph.append(stripped)
        index += 1

    flush_all()
    return "\n".join(output), toc


def render_nav(active: str, prefix: str) -> str:
    links = []
    for label, href in NAV_LINKS:
        target = f"{prefix}{href}"
        class_name = ' class="active"' if label == active else ""
        links.append(f'<a href="{target}"{class_name}>{html.escape(label)}</a>')
    return "".join(links)


def absolute_url(site_url: str, path: str) -> str:
    return f"{site_url.rstrip('/')}/{path.lstrip('/')}"


def render_footer(prefix: str) -> str:
    footer_links = "".join(
        f'<a href="{prefix}{href}">{html.escape(label)}</a>' for label, href in NAV_LINKS[1:]
    )
    return f"""
    <footer class="site-footer">
      <p>Built from local thesis and backtest artifacts in this repository. Designed for Netlify and GitHub Pages deployment.</p>
      <div class="footer-links">{footer_links}</div>
    </footer>
    """


def render_page(
    *,
    title: str,
    description: str,
    active_nav: str,
    prefix: str,
    site_url: str,
    body: str,
    structured_data: dict | None = None,
) -> str:
    json_ld = ""
    if structured_data:
        json_ld = (
            '<script type="application/ld+json">'
            + json.dumps(structured_data, ensure_ascii=False)
            + "</script>"
        )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description, quote=True)}" />
    <meta name="theme-color" content="#173144" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{html.escape(title, quote=True)}" />
    <meta property="og:description" content="{html.escape(description, quote=True)}" />
    <meta property="og:url" content="{html.escape(site_url, quote=True)}" />
    <meta property="og:site_name" content="Thai SET Reverse DCF Research" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="stylesheet" href="{prefix}css/style.css" />
    {json_ld}
  </head>
  <body>
    <div class="site-shell">
      <header class="topbar">
        <a class="brand" href="{prefix}index.html">
          <span class="brand-mark">RDCF</span>
          <span class="brand-copy">
            <strong>Thai SET Reverse DCF</strong>
            <span>Deployment-ready thesis and backtest documentation</span>
          </span>
        </a>
        <nav aria-label="Primary">{render_nav(active_nav, prefix)}</nav>
      </header>
      {body}
      {render_footer(prefix)}
    </div>
  </body>
</html>
"""


def stats_cards(summary_rows: list[dict[str, str]], manifest: dict) -> str:
    ordered = sorted(summary_rows, key=lambda row: float(row["Horizon_Months"]))
    cards = []
    for row in ordered:
        horizon = int(float(row["Horizon_Months"]))
        cards.append(
            f"""
            <div class="metric-card">
              <span>{horizon}-month horizon</span>
              <strong>{pct(float(row["Active_Return"]))}</strong>
              <small>Hit rate {float(row["Hit_Rate"]):.2f}% vs. SET benchmark</small>
            </div>
            """
        )
    cards.append(
        f"""
        <div class="metric-card">
          <span>Audit status</span>
          <strong>{manifest["no_lookahead_failures"]}</strong>
          <small>No-lookahead failures across {manifest["portfolio_rows"]} portfolio rows</small>
        </div>
        """
    )
    return "".join(cards)


def summary_table(summary_rows: list[dict[str, str]]) -> str:
    ordered = sorted(summary_rows, key=lambda row: float(row["Horizon_Months"]))
    rows_html = []
    for row in ordered:
        rows_html.append(
            "<tr>"
            f"<td>{int(float(row['Horizon_Months']))} months</td>"
            f"<td>{pct(float(row['Portfolio_Return']))}</td>"
            f"<td>{pct(float(row['Benchmark_Return']))}</td>"
            f"<td>{pct(float(row['Active_Return']))}</td>"
            f"<td>{float(row['Hit_Rate']):.2f}%</td>"
            "</tr>"
        )
    return """
    <table class="summary-table">
      <thead>
        <tr>
          <th>Horizon</th>
          <th>Portfolio return</th>
          <th>Benchmark return</th>
          <th>Active return</th>
          <th>Hit rate</th>
        </tr>
      </thead>
      <tbody>
    """ + "".join(rows_html) + """
      </tbody>
    </table>
    """


def render_home_page(
    summary_rows: list[dict[str, str]],
    manifest: dict,
    thesis_excerpt_html: str,
    site_url: str,
) -> str:
    body = f"""
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">Thai equities research</span>
        <h1>Reverse DCF evidence for the SET, built for thesis review and production deployment.</h1>
        <p>
          This site packages the repository’s thesis, audited backtest results, and research methodology
          into a fast static site suitable for Netlify or GitHub Pages. The core result is a benchmark-relative
          reverse DCF strategy that stayed positive on average across 3, 6, and 12 month holding periods.
        </p>
        <div class="hero-actions">
          <a class="button primary" href="thesis.html">Read the thesis</a>
          <a class="button secondary" href="backtest/index.html">Inspect the backtest</a>
        </div>
        <div class="pill-row">
          <span class="pill">50-stock audited universe</span>
          <span class="pill">13 quarterly rebalances</span>
          <span class="pill">Damodaran framing</span>
          <span class="pill">Free-data workflow</span>
        </div>
      </div>
      <aside class="hero-panel">
        <h2>Evidence at a glance</h2>
        <div class="metric-grid">
          {stats_cards(summary_rows, manifest)}
        </div>
        <p class="panel-note">
          The stricter audited lane is kept separate from the earlier exploratory simulation so the public site
          can present the strongest evidence without overstating what the data proves.
        </p>
      </aside>
    </section>

    <section class="card-grid">
      <article class="card span-4">
        <p class="kicker">Method</p>
        <h2>Expectation-first valuation</h2>
        <p>
          The workflow starts from market price and solves backward for implied growth, then compares that
          expectation with observed revenue growth, free cash flow, and capital structure data.
        </p>
      </article>
      <article class="card span-4">
        <p class="kicker">Research design</p>
        <h2>No-lookahead controls</h2>
        <p>
          Historical scoring uses dated observations with explicit availability dates, prices on or before the
          rebalance date, and a fixed historical WACC mode to keep the backtest thesis-safe.
        </p>
      </article>
      <article class="card span-4">
        <p class="kicker">Deployment</p>
        <h2>Static, fast, and portable</h2>
        <p>
          The site uses plain HTML and CSS, local assets only, and a reproducible builder so it can deploy on
          Netlify, GitHub Pages, or any static host without a JS toolchain.
        </p>
      </article>
      <article class="card span-6">
        <p class="kicker">Key performance summary</p>
        <h2>Average active return remained positive in every tested horizon.</h2>
        <p>
          The current audited bundle reports positive benchmark-relative returns across all three holding periods,
          with the best average active return at 3 months and the highest hit rate at 6 months.
        </p>
        {summary_table(summary_rows)}
      </article>
      <article class="card span-6">
        <p class="kicker">What this site contains</p>
        <h2>Thesis, research notes, and downloadable artifacts.</h2>
        <ul class="list-clean">
          <li><a href="thesis.html">Complete thesis HTML</a> with a generated table of contents and semantic headings.</li>
          <li><a href="research/index.html">Research methodology page</a> covering data policy, observation dating, and validation logic.</li>
          <li><a href="backtest/index.html">Backtest dashboard</a> with metrics, figures, and audit highlights.</li>
          <li><a href="download/index.html">Download section</a> linking to thesis markdown, CSV summaries, figures, and notes.</li>
        </ul>
      </article>
      <article class="card span-8">
        <p class="kicker">Thesis preview</p>
        <h2>The main argument in one page</h2>
        <div class="content-area">{thesis_excerpt_html}</div>
      </article>
      <article class="card span-4">
        <p class="kicker">Scope</p>
        <h2>How to read the evidence responsibly</h2>
        <ul class="list-clean">
          <li>The exploratory 15.68% CAGR study is retained as context, not as the primary audited proof.</li>
          <li>The audited lane uses a narrower free-data universe and should be treated as the thesis-grade evidence base.</li>
          <li>Exclusion files, audit artifacts, and WACC sensitivity are part of the argument, not optional appendices.</li>
        </ul>
        <p class="callout">The site frames reverse DCF as a disciplined decision framework, not a universal alpha claim.</p>
      </article>
    </section>
    """
    structured_data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Thai SET Reverse DCF Research",
        "url": site_url,
        "description": (
            "Static documentation site for a Thai SET reverse DCF thesis, methodology, and audited backtest results."
        ),
    }
    return render_page(
        title="Thai SET Reverse DCF Research | Thesis and Backtest",
        description=(
            "Deployment-ready site for Thai SET reverse DCF thesis research, no-lookahead backtests, and supporting methodology."
        ),
        active_nav="Home",
        prefix="",
        site_url=site_url,
        body=body,
        structured_data=structured_data,
    )


def render_thesis_page(
    thesis_html: str,
    thesis_toc: list[dict[str, str | int]],
    site_url: str,
) -> str:
    toc_html = "".join(
        f'<li class="level-{item["level"]}"><a href="#{item["id"]}">{html.escape(str(item["text"]))}</a></li>'
        for item in thesis_toc
    )
    body = f"""
    <section class="page-intro">
      <span class="eyebrow">Full thesis</span>
      <h1>Reverse DCF as a Value Investing Framework for Thai SET Markets</h1>
      <p>
        HTML conversion of the repository thesis with semantic headings, tables, code blocks, and internal anchor navigation.
        This page is designed for direct reading, academic review, and search indexing.
      </p>
    </section>
    <section class="content-layout">
      <article class="content-wrap content-area">
        {thesis_html}
      </article>
      <aside class="toc-card" aria-label="Thesis table of contents">
        <h2>On this page</h2>
        <ul class="toc-list">{toc_html}</ul>
      </aside>
    </section>
    """
    structured_data = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": "Reverse DCF as a Value Investing Framework for Thai SET Markets",
        "description": (
            "Thesis evaluating reverse discounted cash flow as a practical value investing framework for Thai SET equities."
        ),
        "url": absolute_url(site_url, "thesis.html"),
        "inLanguage": "en",
        "about": ["Reverse DCF", "Thai SET", "Value investing", "Backtesting"],
    }
    return render_page(
        title="Thesis | Thai SET Reverse DCF",
        description=(
            "Complete thesis on reverse DCF as a value investing framework for Thai SET markets."
        ),
        active_nav="Thesis",
        prefix="",
        site_url=absolute_url(site_url, "thesis.html"),
        body=body,
        structured_data=structured_data,
    )


def render_research_page(
    methodology_html: str,
    datasource_html: str,
    audit_html: str,
    site_url: str,
) -> str:
    body = f"""
    <section class="page-intro">
      <span class="eyebrow">Research architecture</span>
      <h1>Methodology, datasource policy, and validation controls</h1>
      <p>
        The research layer explains how the repository moves from free Thai equity data to dated observations,
        benchmark-relative backtests, and thesis-ready evidence artifacts.
      </p>
    </section>
    <section class="card-grid">
      <article class="card span-8 content-area">
        {methodology_html}
      </article>
      <article class="card span-4">
        <p class="kicker">Why this design</p>
        <h2>Research choices that keep the thesis defensible</h2>
        <ul class="list-clean">
          <li>Free-data only constraint keeps the workflow reproducible.</li>
          <li>Availability-date logic prevents simple timing leakage.</li>
          <li>Explicit exclusions make the investable universe auditable.</li>
          <li>Historical scoring uses fixed WACC to avoid leaking live assumptions into the past.</li>
        </ul>
      </article>
      <article class="card span-6 content-area">
        {datasource_html}
      </article>
      <article class="card span-6 content-area">
        {audit_html}
      </article>
    </section>
    """
    return render_page(
        title="Research Methodology | Thai SET Reverse DCF",
        description=(
            "Methodology, datasource decision, and no-lookahead audit notes for the Thai SET reverse DCF workflow."
        ),
        active_nav="Research",
        prefix="../",
        site_url=absolute_url(site_url, "research/"),
        body=body,
    )


def render_backtest_page(
    summary_rows: list[dict[str, str]],
    sector_rows: list[dict[str, str]],
    wacc_rows: list[dict[str, str]],
    manifest: dict,
    report_html: str,
    appendix_html: str,
    site_url: str,
) -> str:
    sector_sorted = sorted(sector_rows, key=lambda row: float(row["Mean_Active_Return"]), reverse=True)
    strongest = sector_sorted[:3]
    weakest = sector_sorted[-3:]
    wacc_grouped: dict[str, list[dict[str, str]]] = {}
    for row in wacc_rows:
        wacc_grouped.setdefault(row["WACC_Assumption"], []).append(row)

    strongest_items = "".join(
        f"<li>{html.escape(row['Sector'])} at {row['Horizon_Months']} months: {pct(float(row['Mean_Active_Return']))} active return</li>"
        for row in strongest
    )
    weakest_items = "".join(
        f"<li>{html.escape(row['Sector'])} at {row['Horizon_Months']} months: {pct(float(row['Mean_Active_Return']))} active return</li>"
        for row in weakest
    )
    sensitivity_rows = []
    for wacc in sorted(wacc_grouped, key=float):
        best_row = max(wacc_grouped[wacc], key=lambda row: float(row["Active_Return"]))
        sensitivity_rows.append(
            "<tr>"
            f"<td>{float(wacc) * 100:.0f}%</td>"
            f"<td>{best_row['Horizon_Months']} months</td>"
            f"<td>{pct(float(best_row['Active_Return']))}</td>"
            f"<td>{float(best_row['Hit_Rate']):.2f}%</td>"
            "</tr>"
        )

    body = f"""
    <section class="page-intro">
      <span class="eyebrow">Audited performance</span>
      <h1>Benchmark-relative backtest results and visual evidence</h1>
      <p>
        This page packages the thesis-safe outputs: the summary table, no-lookahead status, sector dispersion,
        and WACC sensitivity figures copied into the static site for direct deployment.
      </p>
    </section>
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">Backtest snapshot</span>
        <h1>Positive average active return across all tested holding periods.</h1>
        <p>
          The current implementation uses quarterly rebalancing, top-10 equal weights, benchmark-relative forward
          returns, and fixed WACC historical scoring. It generated {manifest["signals"]} signals with
          {manifest["no_lookahead_failures"]} no-lookahead failures.
        </p>
        {summary_table(summary_rows)}
      </div>
      <aside class="hero-panel">
        <h2>Headline diagnostics</h2>
        <div class="metric-grid">
          {stats_cards(summary_rows, manifest)}
        </div>
        <p class="panel-note">
          Portfolio rows: {manifest["portfolio_rows"]} · Exclusion rows: {manifest["exclusion_rows"]} · Rebalance frequency: {manifest["rebalance_frequency"]}
        </p>
      </aside>
    </section>
    <section class="card-grid">
      <article class="card span-12">
        <p class="kicker">Figures</p>
        <h2>Local chart assets copied into the deploy bundle</h2>
        <div class="figure-grid">
          <figure class="figure-card">
            <img src="../assets/figures/active_return_by_horizon.png" alt="Active return by horizon chart" />
            <figcaption>Average active return stays positive across 3, 6, and 12 month windows.</figcaption>
          </figure>
          <figure class="figure-card">
            <img src="../assets/figures/hit_rate_by_horizon.png" alt="Hit rate by horizon chart" />
            <figcaption>6 month holding periods show the highest hit rate in the current audited sample.</figcaption>
          </figure>
          <figure class="figure-card">
            <img src="../assets/figures/sector_active_return_heatmap.png" alt="Sector active return heatmap" />
            <figcaption>Sector dispersion is large, which supports the thesis framing as a cross-sectional valuation tool.</figcaption>
          </figure>
          <figure class="figure-card">
            <img src="../assets/figures/wacc_sensitivity.png" alt="WACC sensitivity figure" />
            <figcaption>Active returns remain positive under the tested fixed WACC assumptions.</figcaption>
          </figure>
        </div>
      </article>
      <article class="card span-6">
        <p class="kicker">Sector dispersion</p>
        <h2>Best and weakest sector pockets</h2>
        <p class="muted">Best individual sector-horizon combinations in the appendix:</p>
        <ul class="list-clean">{strongest_items}</ul>
        <p class="muted">Weakest individual sector-horizon combinations in the appendix:</p>
        <ul class="list-clean">{weakest_items}</ul>
      </article>
      <article class="card span-6">
        <p class="kicker">WACC sensitivity</p>
        <h2>Best-performing horizon per tested fixed WACC value</h2>
        <table class="summary-table">
          <thead>
            <tr>
              <th>Fixed WACC</th>
              <th>Best horizon</th>
              <th>Best active return</th>
              <th>Hit rate</th>
            </tr>
          </thead>
          <tbody>
            {"".join(sensitivity_rows)}
          </tbody>
        </table>
      </article>
      <article class="card span-6 content-area">
        {report_html}
      </article>
      <article class="card span-6 content-area">
        {appendix_html}
      </article>
    </section>
    """
    return render_page(
        title="Backtest Results | Thai SET Reverse DCF",
        description=(
            "Backtest dashboard for the Thai SET reverse DCF thesis, including summary metrics, figures, and sensitivity analysis."
        ),
        active_nav="Backtest",
        prefix="../",
        site_url=absolute_url(site_url, "backtest/"),
        body=body,
    )


def render_about_page(site_url: str) -> str:
    body = """
    <section class="page-intro">
      <span class="eyebrow">Project overview</span>
      <h1>What this repository is trying to prove, and what it refuses to claim</h1>
      <p>
        The project evaluates whether reverse discounted cash flow can function as a practical value-investing
        framework in Thai equities when the data budget is constrained to free sources.
      </p>
    </section>
    <section class="card-grid">
      <article class="card span-4">
        <p class="kicker">Objective</p>
        <h2>Frame price as an expectation</h2>
        <p>
          Rather than pretending to know the future with precise forecasts, the workflow uses price to infer the
          growth story already embedded in Thai stocks and then tests whether those implied expectations are too high or too low.
        </p>
      </article>
      <article class="card span-4">
        <p class="kicker">Evidence layers</p>
        <h2>Exploratory and audited lanes are separated</h2>
        <p>
          The broad 15.68% CAGR result remains in the repository as exploratory context, while the audited thesis
          bundle serves as the public proof layer because it includes availability dates, benchmark-relative returns,
          and no-lookahead controls.
        </p>
      </article>
      <article class="card span-4">
        <p class="kicker">Constraints</p>
        <h2>Free data, transparent exclusions, modest claims</h2>
        <p>
          Yahoo Finance is used as the primary source because it supports the strongest free historical coverage.
          The site presents the limits alongside the upside so the result is readable without overselling the model.
        </p>
      </article>
      <article class="card span-6">
        <p class="kicker">Audience</p>
        <h2>Built for thesis reviewers, investors, and technical readers</h2>
        <ul class="list-clean">
          <li>Reviewers can read the full thesis and jump to methods, results, and limitations quickly.</li>
          <li>Investors can inspect benchmark-relative evidence, sector behavior, and sensitivity outputs.</li>
          <li>Developers can deploy the static site without a build pipeline and trace each page back to source artifacts in the repo.</li>
        </ul>
      </article>
      <article class="card span-6">
        <p class="kicker">Repository map</p>
        <h2>How the site maps to repo artifacts</h2>
        <ul class="list-clean">
          <li><code>docs/thesis_reverse_dcf_thai_set.md</code> → thesis page</li>
          <li><code>docs/thesis-methodology.md</code> + <code>docs/datasource-decision.md</code> → research page</li>
          <li><code>research_data/latest/backtest/</code> → backtest page and downloads</li>
          <li><code>research_data/latest/thesis_bundle/</code> → downloadable bundle references</li>
        </ul>
      </article>
    </section>
    """
    return render_page(
        title="About | Thai SET Reverse DCF",
        description=(
            "Project overview for the Thai SET reverse DCF thesis and audited backtest documentation site."
        ),
        active_nav="About",
        prefix="../",
        site_url=absolute_url(site_url, "about/"),
        body=body,
    )


def render_download_page(site_url: str) -> str:
    body = """
    <section class="page-intro">
      <span class="eyebrow">Downloads</span>
      <h1>Source files, figures, and summaries copied into the static bundle</h1>
      <p>
        The site ships with local copies of the thesis markdown, executive summary, backtest summaries, and chart assets
        so readers can inspect the primary artifacts without leaving the deployed site.
      </p>
    </section>
    <section class="card-grid">
      <article class="card span-6">
        <p class="kicker">Documents</p>
        <h2>Core markdown sources</h2>
        <ul class="list-clean">
          <li><a href="../assets/docs/thesis_reverse_dcf_thai_set.md">Full thesis markdown</a></li>
          <li><a href="../assets/docs/executive-summary.md">Executive summary</a></li>
          <li><a href="../assets/docs/thesis-methodology.md">Methodology note</a></li>
          <li><a href="../assets/docs/thesis-results.md">Results note</a></li>
          <li><a href="../assets/docs/report.md">Backtest report</a></li>
          <li><a href="../assets/docs/appendix.md">Backtest appendix</a></li>
          <li><a href="../assets/docs/no_lookahead_audit.md">No-lookahead audit</a></li>
        </ul>
      </article>
      <article class="card span-6">
        <p class="kicker">Data extracts</p>
        <h2>CSV outputs for quick review</h2>
        <ul class="list-clean">
          <li><a href="../assets/data/summary.csv">Summary metrics CSV</a></li>
          <li><a href="../assets/data/sector_summary.csv">Sector summary CSV</a></li>
          <li><a href="../assets/data/wacc_sensitivity.csv">WACC sensitivity CSV</a></li>
          <li><a href="../assets/data/exclusions.csv">Exclusions CSV</a></li>
          <li><a href="../assets/data/portfolio_returns.csv">Portfolio returns CSV</a></li>
        </ul>
      </article>
      <article class="card span-12">
        <p class="kicker">Figures</p>
        <h2>Thesis-ready visuals</h2>
        <div class="pill-row">
          <a class="pill" href="../assets/figures/active_return_by_horizon.png">Active return by horizon</a>
          <a class="pill" href="../assets/figures/hit_rate_by_horizon.png">Hit rate by horizon</a>
          <a class="pill" href="../assets/figures/sector_active_return_heatmap.png">Sector heatmap</a>
          <a class="pill" href="../assets/figures/wacc_sensitivity.png">WACC sensitivity</a>
        </div>
      </article>
    </section>
    """
    return render_page(
        title="Download | Thai SET Reverse DCF",
        description=(
            "Download the thesis markdown, summary CSVs, and chart assets for the Thai SET reverse DCF project."
        ),
        active_nav="Download",
        prefix="../",
        site_url=absolute_url(site_url, "download/"),
        body=body,
    )


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def copy_files(mapping: dict[Path, Path]) -> None:
    for source, destination in mapping.items():
        ensure_dir(destination.parent)
        shutil.copy2(source, destination)


def build_sitemap(site_url: str) -> str:
    urls = [
        "",
        "thesis.html",
        "research/",
        "backtest/",
        "about/",
        "download/",
    ]
    entries = []
    for item in urls:
        loc = absolute_url(site_url, item)
        entries.append(
            "  <url>\n"
            f"    <loc>{html.escape(loc)}</loc>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def build_readme(site_url: str) -> str:
    return f"""# Netlify Site Bundle

This directory contains a static documentation site for the Thai SET reverse DCF project.

## What is included

- `index.html` landing page
- `thesis.html` generated thesis page
- `research/index.html` methodology and datasource notes
- `backtest/index.html` results dashboard with local figures
- `about/index.html` project overview
- `download/index.html` document and data downloads
- `css/style.css` shared styling
- `assets/` local copies of documents, figures, and CSV extracts
- `sitemap.xml` and `robots.txt`

## Rebuild

From the repository root:

```bash
python scripts/build_netlify_site.py --site-url {site_url}
```

If you know the production URL, replace the example value above before deployment so `sitemap.xml` and `robots.txt` use the correct base URL.

## Deploy to Netlify

1. Set the publish directory to `netlify/`.
2. No build command is required if the generated files are already committed.
3. If you want Netlify to rebuild the site during deploy, use:

```bash
python scripts/build_netlify_site.py --site-url "$URL"
```

## Deploy to GitHub Pages

1. Publish the `netlify/` directory via the Pages workflow or a `gh-pages` branch.
2. If the site will be served from a subpath, rebuild with the final absolute site URL first.

## Notes

- The site is dependency-free HTML and CSS.
- Asset copies are intentionally local for fast loading and portability.
- The thesis conversion is produced from `docs/thesis_reverse_dcf_thai_set.md`.
"""


def build_asset_sources() -> dict[Path, Path]:
    return {
        ROOT / "research_data/latest/backtest/figures/active_return_by_horizon.png": NETLIFY / "assets/figures/active_return_by_horizon.png",
        ROOT / "research_data/latest/backtest/figures/hit_rate_by_horizon.png": NETLIFY / "assets/figures/hit_rate_by_horizon.png",
        ROOT / "research_data/latest/backtest/figures/sector_active_return_heatmap.png": NETLIFY / "assets/figures/sector_active_return_heatmap.png",
        ROOT / "research_data/latest/backtest/figures/wacc_sensitivity.png": NETLIFY / "assets/figures/wacc_sensitivity.png",
        ROOT / "docs/thesis_reverse_dcf_thai_set.md": NETLIFY / "assets/docs/thesis_reverse_dcf_thai_set.md",
        ROOT / "docs/executive-summary.md": NETLIFY / "assets/docs/executive-summary.md",
        ROOT / "docs/thesis-methodology.md": NETLIFY / "assets/docs/thesis-methodology.md",
        ROOT / "docs/thesis-results.md": NETLIFY / "assets/docs/thesis-results.md",
        ROOT / "docs/damodaran-stern-datasets-thai-set.md": NETLIFY / "assets/docs/damodaran-stern-datasets-thai-set.md",
        ROOT / "research_data/latest/backtest/report.md": NETLIFY / "assets/docs/report.md",
        ROOT / "research_data/latest/backtest/appendix.md": NETLIFY / "assets/docs/appendix.md",
        ROOT / "research_data/latest/backtest/no_lookahead_audit.md": NETLIFY / "assets/docs/no_lookahead_audit.md",
        ROOT / "research_data/latest/backtest/summary.csv": NETLIFY / "assets/data/summary.csv",
        ROOT / "research_data/latest/backtest/sector_summary.csv": NETLIFY / "assets/data/sector_summary.csv",
        ROOT / "research_data/latest/backtest/wacc_sensitivity.csv": NETLIFY / "assets/data/wacc_sensitivity.csv",
        ROOT / "research_data/latest/backtest/exclusions.csv": NETLIFY / "assets/data/exclusions.csv",
        ROOT / "research_data/latest/backtest/portfolio_returns.csv": NETLIFY / "assets/data/portfolio_returns.csv",
        ROOT / "research_data/latest/backtest/manifest.json": NETLIFY / "assets/data/backtest_manifest.json",
        ROOT / "research_data/latest/manifest.json": NETLIFY / "assets/data/research_manifest.json",
        ROOT / "backtest_results/metrics_20260411_133531.txt": NETLIFY / "assets/data/metrics_20260411_133531.txt",
        ROOT / "backtest_results/portfolio_20260411_133531.csv": NETLIFY / "assets/data/portfolio_20260411_133531.csv",
        ROOT / "run_full_backtest.py": NETLIFY / "assets/code/run_full_backtest.py",
        ROOT / "run_simple_backtest.py": NETLIFY / "assets/code/run_simple_backtest.py",
    }


def build_link_map(prefix: str) -> dict[str, str]:
    link_map: dict[str, str] = {}
    for source, destination in build_asset_sources().items():
        if not source.exists():
            continue
        site_path = destination.relative_to(NETLIFY).as_posix()
        target = f"{prefix}{site_path}"
        relative_key = source.relative_to(ROOT).as_posix()
        link_map[str(source)] = target
        link_map[relative_key] = target
    return link_map


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", default=SITE_URL_DEFAULT, help="Absolute production base URL")
    args = parser.parse_args()

    site_url = args.site_url.rstrip("/")

    thesis_md = read_text(ROOT / "docs/thesis_reverse_dcf_thai_set.md")
    methodology_md = read_text(ROOT / "docs/thesis-methodology.md")
    datasource_md = read_text(ROOT / "docs/datasource-decision.md")
    audit_md = read_text(ROOT / "research_data/latest/backtest/no_lookahead_audit.md")
    report_md = read_text(ROOT / "research_data/latest/backtest/report.md")
    appendix_md = read_text(ROOT / "research_data/latest/backtest/appendix.md")

    root_link_map = build_link_map("")
    nested_link_map = build_link_map("../")

    thesis_html, thesis_toc = markdown_to_html(thesis_md, link_map=root_link_map)
    methodology_html, _ = markdown_to_html(methodology_md, toc_levels=(2,), link_map=nested_link_map)
    datasource_html, _ = markdown_to_html(datasource_md, toc_levels=(2,), link_map=nested_link_map)
    audit_html, _ = markdown_to_html(audit_md, toc_levels=(2,), link_map=nested_link_map)
    report_html, _ = markdown_to_html(report_md, toc_levels=(2, 3), link_map=nested_link_map)
    appendix_html, _ = markdown_to_html(appendix_md, toc_levels=(2, 3), link_map=nested_link_map)

    thesis_excerpt = "\n".join(thesis_md.splitlines()[:32])
    thesis_excerpt_html, _ = markdown_to_html(thesis_excerpt, toc_levels=(2,), link_map=root_link_map)

    summary_rows = read_csv(ROOT / "research_data/latest/backtest/summary.csv")
    sector_rows = read_csv(ROOT / "research_data/latest/backtest/sector_summary.csv")
    wacc_rows = read_csv(ROOT / "research_data/latest/backtest/wacc_sensitivity.csv")
    manifest = read_json(ROOT / "research_data/latest/backtest/manifest.json")

    if NETLIFY.exists():
        shutil.rmtree(NETLIFY)

    write_text(NETLIFY / "css/style.css", STYLE_CSS)
    write_text(NETLIFY / "index.html", render_home_page(summary_rows, manifest, thesis_excerpt_html, site_url))
    write_text(NETLIFY / "thesis.html", render_thesis_page(thesis_html, thesis_toc, site_url))
    write_text(
        NETLIFY / "research/index.html",
        render_research_page(methodology_html, datasource_html, audit_html, site_url),
    )
    write_text(
        NETLIFY / "backtest/index.html",
        render_backtest_page(summary_rows, sector_rows, wacc_rows, manifest, report_html, appendix_html, site_url),
    )
    write_text(NETLIFY / "about/index.html", render_about_page(site_url))
    write_text(NETLIFY / "download/index.html", render_download_page(site_url))
    write_text(NETLIFY / "README.md", build_readme(site_url))
    write_text(NETLIFY / "sitemap.xml", build_sitemap(site_url))
    write_text(
        NETLIFY / "robots.txt",
        f"User-agent: *\nAllow: /\n\nSitemap: {absolute_url(site_url, 'sitemap.xml')}\n",
    )

    copy_files({source: destination for source, destination in build_asset_sources().items() if source.exists()})


if __name__ == "__main__":
    main()
