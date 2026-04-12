#!/usr/bin/env python3
"""Build a deployment-ready static documentation site for Netlify/GitHub Pages."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
NETLIFY = ROOT / "netlify"
SITE_URL_DEFAULT = "https://example.com"


NAV_LINKS = [
    ("Home", "index.html"),
    ("Guide (TH)", "guide/index.html"),
    ("Thesis", "thesis.html"),
    ("Research", "research/index.html"),
    ("Backtest", "backtest/index.html"),
    ("About", "about/index.html"),
    ("Download", "download/index.html"),
]


STYLE_CSS = """
/* === Layout & Grid === */
:root {
  --bg: #f4efe5;
  --bg-strong: #efe5d4;
  --paper: rgba(255, 251, 245, 0.9);
  --paper-strong: rgba(253, 248, 240, 0.97);
  --ink: #1f2427;
  --ink-soft: #445057;
  --muted: #596165; /* Darkened for WCAG AA contrast (4.5:1) */
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
  --focus-ring: 0 0 0 3px rgba(180, 86, 47, 0.6);
  --focus-offset: 3px;
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
  font-size: 16px;
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

/* === Navigation & Topbar === */
/* Skip navigation link for keyboard users */
.skip-link {
  position: absolute;
  top: -100px;
  left: 0;
  background: var(--navy);
  color: white;
  padding: 1rem 1.5rem;
  text-decoration: none;
  border-radius: 0 0 var(--radius-md) 0;
  z-index: 9999;
  font-weight: 600;
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: 0;
  outline: var(--focus-ring);
  outline-offset: 0;
}

a {
  color: var(--accent-deep);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.15em;
  transition: color 0.2s ease, opacity 0.2s ease;
}

a:hover {
  color: var(--accent);
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {
  outline: var(--focus-ring);
  outline-offset: var(--focus-offset);
  border-radius: 4px;
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
  padding: 16px 14px 42px; /* Mobile-first padding */
}

@media (min-width: 720px) {
  .site-shell {
    padding: 28px 20px 60px;
  }
}

.topbar {
  display: flex;
  flex-direction: column; /* Mobile-first: stacked */
  gap: 1.25rem;
  margin-bottom: 22px;
  padding: 16px;
  background: rgba(255, 251, 245, 0.74);
  border: 1px solid rgba(40, 50, 58, 0.08);
  border-radius: 26px;
  box-shadow: 0 12px 30px rgba(54, 40, 28, 0.08);
  backdrop-filter: blur(12px);
  z-index: 20;
}

@media (min-width: 720px) {
  .topbar {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 18px 22px;
    border-radius: 999px;
    position: sticky;
    top: 12px;
  }
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  text-decoration: none;
  color: inherit;
  min-height: 48px;
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
  gap: 0.25rem;
}

@media (min-width: 720px) {
  .topbar nav {
    justify-content: flex-end;
    gap: 0.5rem;
  }
}

.topbar nav a {
  padding: 0.65rem 0.9rem;
  border-radius: 999px;
  text-decoration: none;
  font-size: 0.95rem;
  color: var(--ink-soft);
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  transition: background 0.2s ease, color 0.2s ease;
}

.topbar nav a.active,
.topbar nav a:hover {
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
}

/* Breadcrumbs navigation */
.breadcrumbs {
  padding: 0.5rem 0;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.breadcrumbs-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.breadcrumbs-item {
  display: flex;
  align-items: center;
}

.breadcrumbs-item:not(:last-child)::after {
  content: "›";
  color: var(--muted);
  margin-left: 0.5rem;
  font-size: 1.1rem;
}

.breadcrumbs-link {
  color: var(--ink-soft);
  text-decoration: none;
  padding: 0.4rem 0.5rem;
  border-radius: 6px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
}

.breadcrumbs-link:hover {
  background: rgba(23, 49, 68, 0.06);
  color: var(--navy);
  text-decoration: underline;
}

.breadcrumbs-item:last-child .breadcrumbs-link {
  color: var(--ink);
  font-weight: 600;
  pointer-events: none;
}

/* === Hero & Landing === */
.hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 22px;
  margin-bottom: 22px;
}

@media (min-width: 1060px) {
  .hero {
    grid-template-columns: minmax(0, 1.45fr) minmax(290px, 0.95fr);
  }
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
  padding: 22px 20px;
}

@media (min-width: 720px) {
  .hero-copy, .hero-panel, .card, .content-wrap, .page-intro, .site-footer {
    padding: 30px 32px;
  }
}

.hero-copy {
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
  font-size: clamp(2rem, 8vw, 2.7rem);
  line-height: 1.02;
  letter-spacing: -0.03em;
}

@media (min-width: 720px) {
  .hero-copy h1, .page-intro h1 {
    font-size: clamp(2.3rem, 4vw, 4rem);
  }
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
  padding: 0.8rem 1.25rem;
  border-radius: 999px;
  border: 1px solid transparent;
  text-decoration: none;
  font-weight: 600;
  min-height: 48px;
  touch-action: manipulation;
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

/* === Cards & Metrics === */
.metric-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

@media (min-width: 480px) {
  .metric-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
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
  grid-template-columns: 1fr;
  gap: 18px;
  margin-bottom: 22px;
}

@media (min-width: 860px) {
  .card-grid {
    grid-template-columns: repeat(12, 1fr);
  }
  .card.span-4 { grid-column: span 4; }
  .card.span-6 { grid-column: span 6; }
  .card.span-8 { grid-column: span 8; }
  .card.span-12 { grid-column: span 12; }
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

/* Responsive Table Wrapper */
.table-wrapper {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid rgba(40, 50, 58, 0.08);
  margin-top: 1rem;
}

.table-wrapper:focus-visible {
  outline: var(--focus-ring);
  outline-offset: var(--focus-offset);
}

.summary-table {
  width: 100%;
  border-collapse: collapse;
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
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (min-width: 860px) {
  .figure-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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

/* === Timeline & Quarterly === */
.content-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  align-items: start;
}

@media (min-width: 1060px) {
  .content-layout {
    grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
  }
}

.content-wrap {
  padding: 22px 20px;
}

@media (min-width: 720px) {
  .content-wrap {
    padding: 28px 30px;
  }
}

/* === Guide & Sidebar === */
.toc-card {
  padding: 20px;
}

@media (min-width: 1060px) {
  .toc-card {
    position: sticky;
    top: 100px;
  }
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
  padding: 0.45rem 0.6rem;
  border-radius: 0.6rem;
  text-decoration: none;
  color: var(--ink-soft);
}

.toc-list a:hover {
  background: rgba(23, 49, 68, 0.08);
  color: var(--navy);
}

.toc-list .level-3 a {
  padding-left: 1.25rem;
  font-size: 0.93rem;
}

.page-intro {
  margin-bottom: 20px;
}

.content-area h1,
.content-area h2,
.content-area h3,
.content-area h4 {
  scroll-margin-top: 110px;
}

.content-area h1 {
  font-size: clamp(1.8rem, 7vw, 2.35rem);
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
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@media (min-width: 720px) {
  .site-footer {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.site-footer p {
  margin: 0;
  color: var(--ink-soft);
}

.footer-links {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.footer-links a {
  padding: 0.5rem 0.75rem;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
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

.story-grid,
.highlight-grid {
  display: grid;
  gap: 1rem;
}

@media (min-width: 900px) {
  .story-grid {
    grid-template-columns: 1.2fr 0.8fr;
  }

  .highlight-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.qa-card,
.dependency-card,
.timeline-shell {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  box-shadow: var(--shadow);
}

.qa-list {
  margin: 0;
  padding-left: 1.2rem;
}

.timeline-stack {
  display: grid;
  gap: 1rem;
}

.timeline-quarter {
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.55);
  overflow: hidden;
}

.timeline-quarter summary {
  cursor: pointer;
  list-style: none;
  padding: 1rem 1.1rem;
  background: rgba(23, 49, 68, 0.04);
}

.timeline-quarter summary::-webkit-details-marker {
  display: none;
}

.timeline-quarter[open] summary {
  border-bottom: 1px solid var(--line);
}

.timeline-summary-top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: baseline;
}

.timeline-summary-top strong {
  font-size: 1.05rem;
  color: var(--navy);
}

.timeline-summary-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.65rem;
}

.timeline-body {
  padding: 1rem 1.1rem 1.1rem;
  display: grid;
  gap: 1rem;
}

.mini-metrics {
  display: grid;
  gap: 0.85rem;
}

@media (min-width: 760px) {
  .mini-metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.mini-card {
  padding: 0.85rem 0.95rem;
  border-radius: var(--radius-sm);
  background: rgba(23, 49, 68, 0.05);
  border: 1px solid rgba(23, 49, 68, 0.08);
}

.mini-card strong {
  display: block;
  font-size: 1rem;
  color: var(--navy);
  margin-top: 0.2rem;
}

.ticker-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.ticker-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.38rem 0.72rem;
  border-radius: 999px;
  background: rgba(180, 86, 47, 0.1);
  color: var(--accent-deep);
  font-size: 0.92rem;
  font-weight: 600;
}

.timeline-list {
  margin: 0;
  padding-left: 1.15rem;
}

.timeline-list li + li {
  margin-top: 0.45rem;
}

.highlight-card {
  background: rgba(255, 251, 245, 0.92);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 1rem;
}

.highlight-card.accent-profit { border-left: 4px solid var(--success); }
.highlight-card.accent-loss { border-left: 4px solid var(--accent); }
.highlight-card.banned { opacity: 0.6; }

.highlight-card strong {
  display: block;
  color: var(--navy);
  font-size: 1rem;
  margin: 0.1rem 0 0.4rem;
}

.highlight-card p,
.highlight-card small {
  margin: 0;
}

.dependency-list {
  margin: 0.7rem 0 0;
  padding-left: 1.2rem;
}

/* === Responsive Overrides === */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  border: 0;
}

.muted {
  color: var(--muted);
}

/* === Print === */
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
""".strip()


def slugify(text: str) -> str:
    normalized = text.strip().lower()
    slug = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-")
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


THAI_MONTHS = [
    "",
    "ม.ค.",
    "ก.พ.",
    "มี.ค.",
    "เม.ย.",
    "พ.ค.",
    "มิ.ย.",
    "ก.ค.",
    "ส.ค.",
    "ก.ย.",
    "ต.ค.",
    "พ.ย.",
    "ธ.ค.",
]


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def format_date_th(value: str) -> str:
    try:
        parsed = parse_iso_date(value)
    except Exception:
        return value
    return f"{parsed.day} {THAI_MONTHS[parsed.month]} {parsed.year}"


def format_quarter_label(value: str) -> str:
    try:
        parsed = parse_iso_date(value)
    except Exception:
        return value
    quarter = ((parsed.month - 1) // 3) + 1
    return f"ไตรมาส {quarter}/{parsed.year}"


def clean_ticker(value: str) -> str:
    return value.removesuffix(".BK")


def safe_float(value: str | float | int | None, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def rate_text(value: float, digits: int = 1) -> str:
    if abs(value) <= 5:
        return pct(value, digits)
    return "ค่าสูงผิดปกติในข้อมูลปัจจุบัน"


def turnover_text(value: str | float | int | None) -> str:
    numeric = safe_float(value)
    if numeric <= 1:
        return pct(numeric, 0)
    return f"{numeric:.2f}"


def choose_interesting_row(rows: list[dict[str, str]]) -> dict[str, str]:
    sane_rows = [
        row
        for row in rows
        if abs(safe_float(row.get("Signal_Score"))) <= 5
        and abs(safe_float(row.get("Actual_Revenue_Growth"))) <= 5
    ]
    return max(sane_rows or rows, key=lambda row: safe_float(row.get("Signal_Score")))


ENTRY_TEMPLATES = [
    "{ticker}: ใช้{period_type} ณ {stmt_date} — signal gap {signal}. {comparison}",
    "จาก{period_type} ณ {stmt_date}, {ticker} มี signal gap {signal}.{comparison}",
    "{ticker}: งบ{period_type} ({stmt_date}) ทำให้ signal อยู่ที่ {signal}.{comparison}",
]


def format_baht(value: float | str | None) -> str:
    """Thai currency formatting: >= 1e9 -> X.X พันล้านบาท, >= 500k -> X.X ล้านบาท, else -> X บาท."""
    numeric = safe_float(value)
    if abs(numeric) >= 1_000_000_000:
        return f"{numeric / 1_000_000_000:.1f} พันล้านบาท"
    if abs(numeric) >= 500_000:
        return f"{numeric / 1_000_000:.1f} ล้านบาท"
    return f"{numeric:,.0f} บาท"


def calc_margin_of_safety(intrinsic_value: float | str | None, price: float | str | None) -> float | None:
    iv = safe_float(intrinsic_value)
    p = safe_float(price)
    if p <= 0:
        return None
    return (iv - p) / p * 100


def build_exit_narrative(row: dict[str, str]) -> str:
    ticker = clean_ticker(row["Ticker"])
    reason = row.get("Exit_Reason", "rebalance")
    stop_loss = row.get("Stop_Loss_Hit", "False") == "True"
    trigger = safe_float(row.get("Stop_Loss_Trigger_Price"))
    
    thai_reason = "การปรับพอร์ตตามรอบปกติ"
    if reason == "stop_loss" or stop_loss:
        thai_reason = f"ราคาลดลงถึงจุดตัดขาดทุน (Stop-loss) ที่ {trigger:.2f} บาท"
    elif reason == "horizon_end":
        thai_reason = "ครบกำหนดระยะเวลาถือครอง"
        
    return f"{ticker}: ออกจากพอร์ตเนื่องจาก {thai_reason}"


def build_reason_sentences(rows: list[dict[str, str]], entered: set[str], quarter_idx: int = 0) -> list[str]:
    if not rows:
        return []
    entered_rows = [row for row in rows if row["Ticker"] in entered]
    chosen = sorted(
        entered_rows or rows,
        key=lambda row: safe_float(row.get("Signal_Score")),
        reverse=True,
    )[:3]
    sentences = []
    for idx, row in enumerate(chosen):
        ticker = clean_ticker(row["Ticker"])
        period_type = "งบรายไตรมาส" if row.get("Period_Type") == "quarterly" else "งบรายปี"
        statement_date = format_date_th(row.get("Statement_Date", ""))
        signal_score = rate_text(safe_float(row.get("Signal_Score")))
        actual_growth = safe_float(row.get("Actual_Revenue_Growth"))
        implied_growth = safe_float(row.get("Implied_Growth_Rate"))
        
        comparison = ""
        if abs(actual_growth) <= 5 and abs(implied_growth) <= 5:
            comparison = (
                f" รายได้ล่าสุด {pct(actual_growth, 1)} เทียบกับ growth ที่ราคาหุ้นสะท้อน {pct(implied_growth, 1)}."
            )
            
        fcf = safe_float(row.get("FCF"))
        if fcf > 0:
            comparison += f" กระแสเงินสดอิสระ {format_baht(fcf)}."
            
        mos = calc_margin_of_safety(row.get("Intrinsic_Value"), row.get("Price"))
        if mos and abs(mos) > 10:
            comparison += f" ส่วนลดจากมูลค่าพื้นฐาน (MoS) {mos:.1f}%."

        template = ENTRY_TEMPLATES[(quarter_idx + idx) % len(ENTRY_TEMPLATES)]
        sentences.append(
            template.format(
                ticker=ticker,
                period_type=period_type,
                stmt_date=statement_date,
                signal=signal_score,
                comparison=comparison
            )
        )
    return sentences


def build_quarterly_story(backtest_dir: Path) -> dict[str, object]:
    returns_path = backtest_dir / "portfolio_returns.csv"
    returns_lookup = {
        row["Rebalance_Date"]: row
        for row in read_csv(returns_path)
        if row.get("Horizon_Months") == "3"
    } if returns_path.exists() else {}

    files = sorted(backtest_dir.glob("portfolio_*_3m.csv"))
    if not files:
        return {"quarters": [], "highlights": {}}

    quarters: list[dict[str, object]] = []
    all_rows: list[dict[str, str]] = []
    previous_holdings: set[str] = set()
    holding_counter: Counter[str] = Counter()

    for index, path in enumerate(files):
        rows = read_csv(path)
        if not rows:
            continue
        all_rows.extend(rows)
        rebalance_date = rows[0]["Rebalance_Date"]
        holdings = {row["Ticker"] for row in rows}
        holding_counter.update(holdings)
        entered = holdings - previous_holdings
        exited = previous_holdings - holdings
        period_counts = Counter(row.get("Period_Type", "unknown") for row in rows)
        returns_row = returns_lookup.get(rebalance_date, {})
        interesting = choose_interesting_row(rows)
        best = max(rows, key=lambda row: safe_float(row.get("Forward_Return")))
        worst = min(rows, key=lambda row: safe_float(row.get("Forward_Return")))
        quarters.append(
            {
                "rebalance_date": rebalance_date,
                "quarter_label": format_quarter_label(rebalance_date),
                "holdings": sorted(clean_ticker(item) for item in holdings),
                "entered": sorted(clean_ticker(item) for item in entered),
                "exited": sorted(clean_ticker(item) for item in exited),
                "period_summary": ", ".join(
                    f"{'quarterly' if key == 'quarterly' else 'annual'} {value}"
                    for key, value in sorted(period_counts.items())
                ),
                "active_return": safe_float(returns_row.get("Active_Return")),
                "portfolio_return": safe_float(returns_row.get("Portfolio_Return")),
                "benchmark_return": safe_float(returns_row.get("Benchmark_Return")),
                "eligible_count": int(safe_float(returns_row.get("Eligible_Count"))),
                "universe_count": int(safe_float(returns_row.get("Universe_Count"))),
                "turnover": turnover_text(returns_row.get("Turnover")),
                "interesting": interesting,
                "best": best,
                "worst": worst,
                "reasons": build_reason_sentences(rows, entered, index),
                "open": index == len(files) - 1,
            }
        )
        previous_holdings = holdings

    highlights: dict[str, object] = {}
    if all_rows:
        highlights = {
            "interesting_latest": quarters[-1]["interesting"],
            "best_overall": max(all_rows, key=lambda row: safe_float(row.get("Forward_Return"))),
            "worst_overall": min(all_rows, key=lambda row: safe_float(row.get("Forward_Return"))),
            "most_held": holding_counter.most_common(1)[0] if holding_counter else None,
        }

    return {"quarters": quarters, "highlights": highlights}


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
    parts = ['<div class="table-wrapper" tabindex="0" role="region" aria-label="Scrollable data table">', "<table>", "<thead><tr>"]
    parts.extend(f'<th scope="col">{inline_markdown(cell, link_map)}</th>' for cell in header_cells)
    parts.append("</tr></thead><tbody>")
    for row in body_rows:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{inline_markdown(cell, link_map)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
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
        current = ' aria-current="page"' if label == active else ""
        links.append(f'<a href="{target}"{class_name}{current}>{html.escape(label)}</a>')
    return "".join(links)


def render_breadcrumbs(items: list[tuple[str, str]], prefix: str) -> str:
    if len(items) <= 1:
        return ""
    breadcrumbs_html = []
    for i, (label, href) in enumerate(items):
        is_last = i == len(items) - 1
        aria_current = ' aria-current="page"' if is_last else ""
        link_html = f'<span class="breadcrumbs-link"{aria_current}>{html.escape(label)}</span>' if is_last else f'<a href="{prefix}{href}" class="breadcrumbs-link">{html.escape(label)}</a>'
        breadcrumbs_html.append(f'<li class="breadcrumbs-item">{link_html}</li>')
    
    return f"""
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <ol class="breadcrumbs-list">
        {''.join(breadcrumbs_html)}
      </ol>
    </nav>
    """


def absolute_url(site_url: str, path: str) -> str:
    return f"{site_url.rstrip('/')}/{path.lstrip('/')}"


def render_footer(prefix: str) -> str:
    footer_links = "".join(
        f'<a href="{prefix}{href}">{html.escape(label)}</a>' for label, href in NAV_LINKS[1:]
    )
    return f"""
    <footer class="site-footer">
      <p>Built from local thesis and backtest artifacts in this repository. Designed for Netlify and GitHub Pages deployment.</p>
      <nav class="footer-links" aria-label="Footer">{footer_links}</nav>
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
    lang: str = "en",
    breadcrumbs: list[tuple[str, str]] | None = None,
    structured_data: dict | None = None,
) -> str:
    json_ld = ""
    if structured_data:
        json_ld = (
            '<script type="application/ld+json">'
            + json.dumps(structured_data, ensure_ascii=False)
            + "</script>"
        )
    
    breadcrumbs_markup = render_breadcrumbs(breadcrumbs, prefix) if breadcrumbs else ""

    return f"""<!doctype html>
<html lang="{html.escape(lang, quote=True)}">
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
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <div class="site-shell">
      <header class="topbar">
        <a class="brand" href="{prefix}index.html" aria-label="Thai SET Reverse DCF Research - Home">
          <span class="brand-mark">RDCF</span>
          <span class="brand-copy">
            <strong>Thai SET Reverse DCF</strong>
            <span>Deployment-ready thesis and backtest documentation</span>
          </span>
        </a>
        <nav aria-label="Primary">{render_nav(active_nav, prefix)}</nav>
      </header>
      {breadcrumbs_markup}
      <main id="main-content">
        {body}
      </main>
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
    <div class="table-wrapper" tabindex="0" role="region" aria-label="Backtest performance summary table">
    <table class="summary-table">
      <thead>
        <tr>
          <th scope="col">Horizon</th>
          <th scope="col">Portfolio return</th>
          <th scope="col">Benchmark return</th>
          <th scope="col">Active return</th>
          <th scope="col">Hit rate</th>
        </tr>
      </thead>
      <tbody>
    """ + "".join(rows_html) + """
      </tbody>
    </table>
    </div>
    """


def render_ticker_pills(items: list[str]) -> str:
    if not items:
        return '<p class="muted">ไม่มีการเปลี่ยนแปลง</p>'
    return '<div class="ticker-pills">' + "".join(
        f'<span class="ticker-pill">{html.escape(item)}</span>' for item in items
    ) + "</div>"


def render_highlight_card(label: str, row: dict[str, str], extra: str) -> str:
    fcf = safe_float(row.get("FCF"))
    mos = calc_margin_of_safety(row.get("Intrinsic_Value"), row.get("Price"))
    forward_return = safe_float(row.get("Forward_Return"))
    buy_ban = row.get("Buy_Ban_Active", "False") == "True"
    
    classes = ["highlight-card"]
    if forward_return > 0:
        classes.append("accent-profit")
    elif forward_return < 0:
        classes.append("accent-loss")
    if buy_ban:
        classes.append("banned")
        
    details = []
    if fcf > 0:
        details.append(f"FCF: {format_baht(fcf)}")
    if mos and abs(mos) > 0.1:
        details.append(f"MoS: {mos:.1f}%")
    if buy_ban:
        details.append("⚠️ Buy Ban Active")
        
    details_html = f"<p class='muted'><small>{' | '.join(details)}</small></p>" if details else ""

    return f"""
    <article class='{' '.join(classes)}'>
      <span class="eyebrow">{html.escape(label)}</span>
      <strong>{html.escape(clean_ticker(row["Ticker"]))}</strong>
      <p>{extra}</p>
      {details_html}
      <small>รอบลงทุน {html.escape(format_date_th(row["Rebalance_Date"]))}</small>
    </article>
    """


GUIDE_FAQ = [
    {
        "q": "Reverse DCF คืออะไร?",
        "a": "คือการคำนวณย้อนกลับจากราคาหุ้นในตลาด เพื่อหาว่านักลงทุนกำลังคาดหวังการเติบโตของกำไรหรือกระแสเงินสดเท่าไหร่ แล้วจึงนำมาเทียบกับตัวเลขจริงที่บริษัททำได้เพื่อให้เห็นว่าหุ้นแพงหรือถูกเกินไปจากความคาดหวังนั้น",
    },
    {
        "q": "ทำไมต้องเน้นหุ้นใน SET100?",
        "a": "เพราะเป็นกลุ่มหุ้นที่มีสภาพคล่องสูงและมีการเปิดเผยข้อมูลพื้นฐานสม่ำเสมอเพียงพอที่จะนำมาสร้างโมเดลย้อนกลับ (Reverse) ได้อย่างน่าเชื่อถือเมื่อเทียบกับหุ้นขนาดเล็ก",
    },
    {
        "q": "พอร์ตลงทุนปรับเปลี่ยนทุกไตรมาสหมายถึงอะไร?",
        "a": "โมเดลจะทำการตรวจสอบงบการเงินล่าสุดที่ประกาศออกมาทุก 3 เดือน หากพื้นฐานเปลี่ยนไปจนทำให้ความคาดหวังในราคาหุ้นไม่สมเหตุสมผล พอร์ตจะทำการหมุนเวียนหุ้น (Rebalance) ทันที",
    },
    {
        "q": "ความเสี่ยงที่สำคัญที่สุดคืออะไร?",
        "a": "คือความถูกต้องและรวดเร็วของข้อมูล (Data Lag) รวมถึงความผันผวนของตลาดในระยะสั้นที่อาจไม่สะท้อนพื้นฐานทันที เราจึงต้องใช้การถือครอง 3-12 เดือนเพื่อรอให้ราคาตอบสนองต่อพื้นฐาน",
    },
]


def render_guide_toc(body_html: str) -> str:
    """Extract h2 headings from body and render a sticky sidebar TOC using existing toc-card classes."""
    headings = re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', body_html)
    if not headings:
        return ""

    links = []
    for h_id, h_text in headings:
        links.append(f'<li><a href="#{h_id}">{html.escape(h_text)}</a></li>')

    return f"""
    <aside class="toc-card" aria-label="สารบัญเนื้อหา">
      <h2>ในหน้านี้</h2>
      <ul class="toc-list">
        {''.join(links)}
      </ul>
    </aside>
    """


def render_reader_guide_page(
    intro_html: str,
    story: dict[str, object],
    research_manifest: dict,
    backtest_manifest: dict,
    site_url: str,
) -> str:
    quarters: list[dict[str, object]] = story.get("quarters", [])  # type: ignore[assignment]
    highlights: dict[str, object] = story.get("highlights", {})  # type: ignore[assignment]
    current_rows = research_manifest.get("rows", {})
    current_tickers = int(current_rows.get("fundamentals", 0))
    current_observations = int(current_rows.get("observations", 0))

    highlight_markup = ""
    if highlights:
        interesting_latest = highlights["interesting_latest"]  # type: ignore[index]
        best_overall = highlights["best_overall"]  # type: ignore[index]
        worst_overall = highlights["worst_overall"]  # type: ignore[index]
        most_held = highlights.get("most_held")
        highlight_markup = f"""
        <section class="highlight-grid">
          {render_highlight_card(
              "หุ้นเด่นล่าสุด",
              interesting_latest,
              f"คะแนน signal สูงสุดในรอบล่าสุด ({rate_text(safe_float(interesting_latest['Signal_Score']))})",
          )}
          {render_highlight_card(
              "กำไรมากสุดจาก output ปัจจุบัน",
              best_overall,
              f"ผลตอบแทน 3 เดือน {pct(safe_float(best_overall['Forward_Return']))} และ active return {pct(safe_float(best_overall['Active_Return']))}",
          )}
          {render_highlight_card(
              "ขาดทุนมากสุดจาก output ปัจจุบัน",
              worst_overall,
              f"ผลตอบแทน 3 เดือน {pct(safe_float(worst_overall['Forward_Return']))} และ active return {pct(safe_float(worst_overall['Active_Return']))}",
          )}
        """
        if most_held:
            ticker, count = most_held
            highlight_markup += f"""
          <article class="highlight-card">
            <span class="eyebrow">หุ้นที่ถูกถือบ่อยสุด</span>
            <strong>{html.escape(clean_ticker(str(ticker)))}</strong>
            <p>ติดพอร์ต {count} รอบใน timeline 3 เดือนที่มีอยู่ตอนนี้</p>
            <small>ใช้เพื่ออธิบายความสม่ำเสมอของ model ก่อนมี output final ชุดใหม่</small>
          </article>
            """
        highlight_markup += "</section>"
    else:
        highlight_markup = """
        <section class="dependency-card">
          <h2>ส่วนไฮไลต์หุ้นยังรอ output</h2>
          <p>ถ้ายังไม่มีไฟล์ <code>portfolio_YYYY-MM-DD_3m.csv</code> ตัว build จะขึ้นโครงสร้าง placeholder ไว้ก่อน และรอ output backtest รอบใหม่เข้ามาเติม.</p>
        </section>
        """

    if quarters:
        timeline_items = []
        for quarter in quarters:
            interesting = quarter["interesting"]  # type: ignore[index]
            best = quarter["best"]  # type: ignore[index]
            worst = quarter["worst"]  # type: ignore[index]
            reasons_html = "".join(
                f"<li>{html.escape(item)}</li>" for item in quarter["reasons"]  # type: ignore[index]
            ) or "<li>รอ output attribution ที่ละเอียดกว่านี้จากฝั่ง backtest engine</li>"
            open_attr = " open" if quarter["open"] else ""
            timeline_items.append(
                f"""
                <details class="timeline-quarter"{open_attr} id="quarter-{html.escape(str(quarter['rebalance_date']))}">
                  <summary>
                    <div class="timeline-summary-top">
                      <strong>{html.escape(str(quarter['quarter_label']))} · รอบลงทุน {html.escape(format_date_th(str(quarter['rebalance_date'])))}</strong>
                      <span>{html.escape(' | '.join([f'Active return {pct(float(quarter["active_return"]))}', f'เข้า {len(quarter["entered"])} ตัว', f'ออก {len(quarter["exited"])} ตัว']))}</span>
                    </div>
                    <div class="timeline-summary-meta">
                      <span class="ticker-pill">ถือ {len(quarter['holdings'])} หุ้น</span>
                      <span class="ticker-pill">Universe {quarter['universe_count']}</span>
                      <span class="ticker-pill">Eligible {quarter['eligible_count']}</span>
                      <span class="ticker-pill">Turnover {html.escape(str(quarter['turnover']))}</span>
                    </div>
                  </summary>
                  <div class="timeline-body">
                    <div class="mini-metrics">
                      <div class="mini-card"><span>พอร์ตที่ถือ</span><strong>{len(quarter['holdings'])} หุ้น</strong><small>{html.escape(str(quarter['period_summary']))}</small></div>
                      <div class="mini-card"><span>ผลตอบแทนพอร์ต</span><strong>{pct(float(quarter['portfolio_return']))}</strong><small>เทียบ benchmark {pct(float(quarter['benchmark_return']))}</small></div>
                      <div class="mini-card"><span>คำตอบของไตรมาสนี้</span><strong>{html.escape(clean_ticker(interesting['Ticker']))}</strong><small>หุ้นที่คะแนน signal เด่นสุดในรอบนี้</small></div>
                    </div>
                    <div>
                      <h3>ถืออะไรอยู่บ้าง</h3>
                      {render_ticker_pills(quarter['holdings'])}
                    </div>
                    <div>
                      <h3>เข้าใหม่ / ออก</h3>
                      <p><strong>เข้าใหม่</strong></p>
                      {render_ticker_pills(quarter['entered'])}
                      <p><strong>ออกจากพอร์ต</strong></p>
                      {render_ticker_pills(quarter['exited'])}
                    </div>
                    <div>
                      <h3>fundamental เปลี่ยนแล้วพอร์ตเปลี่ยนอย่างไร</h3>
                      <ul class="timeline-list">{reasons_html}</ul>
                    </div>
                    <div class="highlight-grid">
                      {render_highlight_card("หุ้นเด่นของไตรมาส", interesting, f"signal gap {rate_text(safe_float(interesting['Signal_Score']))} จากงบ {interesting['Period_Type']}")}
                      {render_highlight_card("กำไรมากสุดในไตรมาส", best, f"ผลตอบแทน 3 เดือน {pct(safe_float(best['Forward_Return']))}")}
                      {render_highlight_card("ขาดทุนมากสุดในไตรมาส", worst, f"ผลตอบแทน 3 เดือน {pct(safe_float(worst['Forward_Return']))}")}
                    </div>
                  </div>
                </details>
                """
            )
        timeline_markup = f"""
        <section class="timeline-shell">
          <div class="page-intro">
            <span class="eyebrow">Quarterly timeline</span>
            <h2 id="quarterly-timeline">เส้นเวลา “ถือ / เข้า / ออก / ทำไมเปลี่ยน”</h2>
            <p>ส่วนนี้อ่านตามรอบ rebalance รายไตรมาส โดยยึดไฟล์พอร์ต 3 เดือนเพื่อให้เล่าเรื่องการเปลี่ยนพอร์ตเป็นลำดับเวลาเดียวกันก่อน เมื่อ output case ใหม่พร้อมแล้ว โครงนี้จะ reuse ได้ทันที.</p>
          </div>
          <div class="timeline-stack">
            {''.join(timeline_items)}
          </div>
        </section>
        """
    else:
        timeline_markup = """
        <section class="timeline-shell">
          <h2 id="quarterly-timeline">Quarterly timeline template พร้อมแล้ว แต่ยังรอ output</h2>
          <p>ตัว site builder รองรับ timeline รายไตรมาสแล้ว หากยังไม่มีไฟล์พอร์ต 3 เดือน (`portfolio_YYYY-MM-DD_3m.csv`) จะขึ้น placeholder นี้แทนเพื่อไม่ให้ docs lane block upstream work.</p>
          <ul class="dependency-list">
            <li>ต้องมีไฟล์พอร์ตต่อรอบ rebalance อย่างน้อยหนึ่ง horizon ที่เล่า timeline ได้</li>
            <li>ต้องมี `portfolio_returns.csv` เพื่อเติม universe / eligible / turnover</li>
            <li>ถ้าต้องการเหตุผลเปลี่ยนหุ้นที่คมกว่าเดิม ต้องมี output attribution จาก backtest engine</li>
          </ul>
        </section>
        """

    faq_items = []
    for item in GUIDE_FAQ:
        faq_items.append(
            f"""
            <details class="timeline-quarter">
              <summary><strong>{html.escape(item['q'])}</strong></summary>
              <div class="timeline-body"><p>{html.escape(item['a'])}</p></div>
            </details>
            """
        )
    faq_markup = f"""
    <section class="timeline-shell">
      <div class="page-intro">
        <span class="eyebrow">FAQ</span>
        <h2 id="faq">คำถามที่พบบ่อย (Investor FAQ)</h2>
      </div>
      <div class="timeline-stack">
        {''.join(faq_items)}
      </div>
    </section>
    """

    body_content = f"""
    <section class="hero" aria-labelledby="guide-th-title">
      <div class="hero-copy">
        <span class="eyebrow">คู่มือภาษาไทยแบบ reader-first</span>
        <h1 id="guide-th-title">เริ่มจากคำถามที่ชัด แล้วค่อยไล่ดูคำตอบผ่าน timeline การลงทุนรายไตรมาส</h1>
        <p>
          หน้านี้เป็นประตูหลักสำหรับนักลงทุนและคนทั่วไป: บอกให้ชัดว่าโปรเจกต์กำลังพิสูจน์อะไร,
          ควรอ่านหลักฐานอย่างไร, และพอร์ตเปลี่ยนเมื่อ fundamentals เปลี่ยนตรงไหนบ้าง.
        </p>
        <div class="hero-actions">
          <a class="button primary" href="../backtest/index.html">ดูผล backtest ที่มีอยู่ตอนนี้</a>
          <a class="button secondary" href="../download/index.html">ดาวน์โหลดไฟล์อ้างอิง</a>
        </div>
      </div>
      <aside class="hero-panel">
        <h2>สถานะ surface นี้</h2>
        <div class="metric-grid">
          <div class="metric-card">
            <span>Current repo bundle</span>
            <strong>{current_tickers}</strong>
            <small>ticker ใน output ล่าสุดที่ builder อ่านได้ตอนนี้</small>
          </div>
          <div class="metric-card">
            <span>Quarterly timeline</span>
            <strong>{len(quarters)}</strong>
            <small>รอบ rebalance ที่เล่าได้จากไฟล์พอร์ต 3 เดือน</small>
          </div>
          <div class="metric-card">
            <span>Observations</span>
            <strong>{current_observations}</strong>
            <small>dated observations ที่มีใน bundle ปัจจุบัน</small>
          </div>
          <div class="metric-card">
            <span>Backtest rows</span>
            <strong>{backtest_manifest.get('portfolio_rows', 0)}</strong>
            <small>แถวพอร์ตจาก output ล่าสุดใน repo</small>
          </div>
        </div>
        <p class="panel-note">โครงหน้านี้ทำให้ docs/site เดินหน้าได้ก่อน แม้ output 100 หุ้น + rules ใหม่จะยังไม่ build เสร็จจาก lane data/backtest.</p>
      </aside>
    </section>

    <section class="story-grid">
      <article class="qa-card content-area">
        <h2 id="core-question">คำถามหลักที่งานนี้ต้องตอบ</h2>
        {intro_html}
      </article>
      <aside class="dependency-card">
        <span class="eyebrow">สิ่งที่หน้าเว็บนี้ตอบให้ได้ทันที</span>
        <ol class="qa-list">
          <li><a href="#core-question">เรากำลังพิสูจน์อะไร และคำตอบสั้นตอนนี้คืออะไร</a></li>
          <li><a href="#quarterly-timeline">ไตรมาสไหนพอร์ตถืออะไร เข้าอะไร ออกอะไร</a></li>
          <li>หุ้นไหนเด่นสุด / กำไรมากสุด / ขาดทุนมากสุด</li>
          <li><a href="#dependencies">ส่วนไหนยังต้องรอ output final จาก upstream lanes</a></li>
          <li><a href="#faq">คำถามที่พบบ่อย (FAQ)</a></li>
        </ol>
      </aside>
    </section>

    {highlight_markup}
    {timeline_markup}
    {faq_markup}

    <section class="dependency-card" id="dependencies">
      <span class="eyebrow">Dependencies ที่ยังต้องรอจาก lanes อื่น</span>
      <h2>สิ่งที่ต้องเข้ามาเติมก่อนหน้า public final จะสมบูรณ์</h2>
      <ul class="dependency-list">
        <li>output ชุด <strong>100 หุ้นแบบ multi-source</strong> ที่ใช้ scraping เป็นแกนและเติม yfinance เมื่อจำเป็น</li>
        <li>ผล backtest final ตามแผน Damodaran 2 case: baseline และ risk-control พร้อม Top 5 / Top 10 / SL 5% / 10%</li>
        <li>กติกา “แพ้เกิน 2 buy rounds แล้วห้ามซื้ออีก” จาก backtest engine รอบใหม่</li>
        <li>stock-change attribution ที่ละเอียดกว่า signal summary ถ้าฝั่ง engine ส่งเหตุผลระดับ factor/metric ออกมาได้</li>
        <li>บทสรุป thesis/public wording รอบสุดท้ายหลังเลข final นิ่งแล้ว</li>
      </ul>
    </section>
    """

    toc_markup = render_guide_toc(body_content)

    final_body = f"""
    <div class="content-layout">
      <div class="content-wrap">
        {body_content}
      </div>
      {toc_markup}
    </div>
    """

    structured_data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "headline": "คู่มือภาษาไทยแบบ reader-first สำหรับ Reverse DCF ตลาดหุ้นไทย",
        "description": "หน้าสรุปภาษาไทยที่อธิบายสิ่งที่โปรเจกต์ต้องการพิสูจน์ พร้อม quarterly timeline การลงทุนและไฮไลต์หุ้นเด่น",
        "url": absolute_url(site_url, "guide/"),
        "inLanguage": "th",
    }
    return render_page(
        title="คู่มือภาษาไทย | Thai SET Reverse DCF",
        description="หน้าสรุปภาษาไทยสำหรับนักลงทุนและคนทั่วไป พร้อม quarterly timeline และ stock highlights",
        active_nav="Guide (TH)",
        prefix="../",
        site_url=absolute_url(site_url, "guide/"),
        body=final_body,
        lang="th",
        breadcrumbs=[("Home", "index.html"), ("Guide (TH)", "guide/index.html")],
        structured_data=structured_data,
    )



def render_home_page(
    summary_rows: list[dict[str, str]],
    manifest: dict,
    thesis_excerpt_html: str,
    site_url: str,
) -> str:
    body = f"""
    <section class="hero" aria-labelledby="hero-heading">
      <div class="hero-copy">
        <span class="eyebrow">Thai equities research</span>
        <h1 id="hero-heading">Reverse DCF evidence for the SET, built for thesis review and production deployment.</h1>
        <p>
          This site packages the repository’s thesis, audited backtest results, and research methodology
          into a fast static site suitable for Netlify or GitHub Pages. The core result is a benchmark-relative
          reverse DCF strategy that stayed positive on average across 3, 6, and 12 month holding periods.
        </p>
        <div class="hero-actions">
          <a class="button primary" href="guide/index.html">Read the Thai guide</a>
          <a class="button secondary" href="backtest/index.html">Inspect the backtest</a>
        </div>
        <div class="pill-row">
          <span class="pill">Reader-first Thai guide</span>
          <span class="pill">13 quarterly rebalances</span>
          <span class="pill">Damodaran framing</span>
          <span class="pill">Current repo bundle</span>
        </div>
      </div>
      <aside class="hero-panel">
        <h2>Evidence at a glance</h2>
        <div class="metric-grid">
          {stats_cards(summary_rows, manifest)}
        </div>
        <p class="panel-note">
          The site now has a reader-first Thai surface for investors and general readers, while the thesis and
          audited outputs remain available as supporting layers behind it.
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
        <p class="kicker">Reader-first layer</p>
        <h2>Start with the Thai guide if you want the short answer first.</h2>
        <p>
          The new Guide (TH) page is organized around the core proof question, quarterly portfolio timeline,
          and stock highlights so non-academic readers can understand the argument before diving into raw artifacts.
        </p>
      </article>
      <article class="card span-6">
        <p class="kicker">What this site contains</p>
        <h2>Thesis, research notes, and downloadable artifacts.</h2>
        <ul class="list-clean">
          <li><a href="guide/index.html">Thai guide</a> that answers the core proof question with a quarterly narrative.</li>
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
          <li>The reader-first guide intentionally avoids locking in a final public proof set until the 100-stock rebuild is ready.</li>
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
        breadcrumbs=[("Home", "index.html")],
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
    <section class="page-intro" aria-labelledby="thesis-title">
      <span class="eyebrow">Full thesis</span>
      <h1 id="thesis-title">Reverse DCF as a Value Investing Framework for Thai SET Markets</h1>
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
        breadcrumbs=[("Home", "index.html"), ("Thesis", "thesis.html")],
        structured_data=structured_data,
    )


def render_research_page(
    methodology_html: str,
    datasource_html: str,
    audit_html: str,
    site_url: str,
) -> str:
    body = f"""
    <section class="page-intro" aria-labelledby="research-title">
      <span class="eyebrow">Research architecture</span>
      <h1 id="research-title">Methodology, datasource policy, and validation controls</h1>
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
        breadcrumbs=[("Home", "index.html"), ("Research", "research/index.html")],
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
    <section class="page-intro" aria-labelledby="backtest-title">
      <span class="eyebrow">Audited performance</span>
      <h1 id="backtest-title">Benchmark-relative backtest results and visual evidence</h1>
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
        <div class="table-wrapper" tabindex="0" role="region" aria-label="WACC sensitivity summary table">
        <table class="summary-table">
          <thead>
            <tr>
              <th scope="col">Fixed WACC</th>
              <th scope="col">Best horizon</th>
              <th scope="col">Best active return</th>
              <th scope="col">Hit rate</th>
            </tr>
          </thead>
          <tbody>
            {"".join(sensitivity_rows)}
          </tbody>
        </table>
        </div>
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
        breadcrumbs=[("Home", "index.html"), ("Backtest", "backtest/index.html")],
    )


def render_about_page(site_url: str) -> str:
    body = """
    <section class="page-intro" aria-labelledby="about-title">
      <span class="eyebrow">Project overview</span>
      <h1 id="about-title">What this repository is trying to prove, and what it refuses to claim</h1>
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
        <h2>Built first for investors and general readers, then for reviewers</h2>
        <ul class="list-clean">
          <li>General readers can start with the Thai guide and understand the proof question before reading technical details.</li>
          <li>Investors can inspect benchmark-relative evidence, sector behavior, and sensitivity outputs.</li>
          <li>Reviewers can still read the full thesis and jump to methods, results, and limitations quickly.</li>
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
        breadcrumbs=[("Home", "index.html"), ("About", "about/index.html")],
    )


def render_download_page(site_url: str) -> str:
    body = """
    <section class="page-intro" aria-labelledby="download-title">
      <span class="eyebrow">Downloads</span>
      <h1 id="download-title">Source files, figures, and summaries copied into the static bundle</h1>
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
          <li><a href="../assets/docs/reader-first-thai.md">Thai reader-first guide source</a></li>
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
        breadcrumbs=[("Home", "index.html"), ("Download", "download/index.html")],
    )


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def copy_files(mapping: dict[Path, Path]) -> None:
    for source, destination in mapping.items():
        ensure_dir(destination.parent)
        shutil.copy2(source, destination)


def build_sitemap(site_url: str) -> str:
    urls = [""]
    for _, href in NAV_LINKS[1:]:
        urls.append(href.removesuffix("index.html"))
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
- `guide/index.html` Thai reader-first guide
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
        ROOT / "docs/reader-first-thai.md": NETLIFY / "assets/docs/reader-first-thai.md",
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

    reader_guide_md = read_text(ROOT / "docs/reader-first-thai.md")
    thesis_md = read_text(ROOT / "docs/thesis_reverse_dcf_thai_set.md")
    methodology_md = read_text(ROOT / "docs/thesis-methodology.md")
    datasource_md = read_text(ROOT / "docs/datasource-decision.md")
    audit_md = read_text(ROOT / "research_data/latest/backtest/no_lookahead_audit.md")
    report_md = read_text(ROOT / "research_data/latest/backtest/report.md")
    appendix_md = read_text(ROOT / "research_data/latest/backtest/appendix.md")

    root_link_map = build_link_map("")
    nested_link_map = build_link_map("../")

    reader_guide_html, _ = markdown_to_html(reader_guide_md, toc_levels=(2, 3), link_map=nested_link_map)
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
    research_manifest = read_json(ROOT / "research_data/latest/manifest.json")
    quarterly_story = build_quarterly_story(ROOT / "research_data/latest/backtest")

    if NETLIFY.exists():
        shutil.rmtree(NETLIFY)

    write_text(NETLIFY / "css/style.css", STYLE_CSS)
    write_text(NETLIFY / "index.html", render_home_page(summary_rows, manifest, thesis_excerpt_html, site_url))
    write_text(
        NETLIFY / "guide/index.html",
        render_reader_guide_page(reader_guide_html, quarterly_story, research_manifest, manifest, site_url),
    )
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
