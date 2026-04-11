from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd


PRIMARY_SOURCE_ID = "yahoo_yfinance"


@dataclass(frozen=True)
class SourceAssessment:
    id: str
    label: str
    role: str
    completeness_rank: int
    automation_rank: int
    status: str
    rationale: str


SOURCE_ASSESSMENTS: Sequence[SourceAssessment] = (
    SourceAssessment(
        id=PRIMARY_SOURCE_ID,
        label="Yahoo Finance via yfinance",
        role="primary",
        completeness_rank=1,
        automation_rank=1,
        status="chosen",
        rationale="Best balance of free historical coverage, scriptability, and existing repo support for repeatable backtests.",
    ),
    SourceAssessment(
        id="set_website_scraping",
        label="SET website scraping",
        role="validation",
        completeness_rank=3,
        automation_rank=3,
        status="validation_only",
        rationale="Useful for official spot checks, but bulk historical depth and scraper stability are weaker than the primary Yahoo path.",
    ),
    SourceAssessment(
        id="investing_com_scraping",
        label="Investing.com scraping",
        role="fallback",
        completeness_rank=2,
        automation_rank=4,
        status="rejected",
        rationale="Can help with ad hoc market-history checks, but HTML scraping is brittle and less reusable for a single-source research pipeline.",
    ),
    SourceAssessment(
        id="smartxl_trial",
        label="SmartXL trial workflow",
        role="fallback",
        completeness_rank=4,
        automation_rank=5,
        status="rejected",
        rationale="Trial-based spreadsheet access is not durable enough for a reproducible free pipeline or unattended refresh jobs.",
    ),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def source_review_payload() -> Dict[str, object]:
    chosen = [assessment for assessment in SOURCE_ASSESSMENTS if assessment.status == "chosen"]
    alternatives = [assessment for assessment in SOURCE_ASSESSMENTS if assessment.status != "chosen"]
    return {
        "decision_rule": "Prefer the strongest free datasource for historical backtest completeness; keep official/manual sources optional.",
        "chosen_source": asdict(chosen[0]),
        "alternatives": [asdict(item) for item in alternatives],
    }


def summarize_quality(
    quality_report: pd.DataFrame,
    exclusion_report: pd.DataFrame,
    fundamental_coverage: pd.DataFrame,
    price_coverage: pd.DataFrame,
) -> Dict[str, object]:
    if not quality_report.empty and "Required_For_Reverse_DCF" in quality_report.columns:
        required_fields = quality_report.loc[quality_report["Required_For_Reverse_DCF"], "Field"].tolist()
    else:
        required_fields = []
    excluded = 0
    if not exclusion_report.empty and "Passes_Reverse_DCF_Filter" in exclusion_report.columns:
        excluded = int((~exclusion_report["Passes_Reverse_DCF_Filter"]).sum())
    missing_fundamentals = []
    if not fundamental_coverage.empty and "Has_Fundamental_Observations" in fundamental_coverage.columns:
        missing_fundamentals = fundamental_coverage.loc[
            ~fundamental_coverage["Has_Fundamental_Observations"], "Ticker"
        ].tolist()
    missing_prices = []
    if not price_coverage.empty and "Has_Prices" in price_coverage.columns:
        missing_prices = price_coverage.loc[~price_coverage["Has_Prices"], "Ticker"].tolist()
    return {
        "required_fields": required_fields,
        "excluded_ticker_count": excluded,
        "missing_fundamental_tickers": missing_fundamentals,
        "missing_price_tickers": missing_prices,
    }


def append_acquisition_log(path: Path, record: Dict[str, object]) -> None:
    entries: List[Dict[str, object]]
    if path.exists():
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            entries = [entries]
    else:
        entries = []
    entries.append(record)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def file_inventory(paths: Dict[str, Path]) -> List[Dict[str, object]]:
    items = []
    for label, path in sorted(paths.items()):
        if not path.exists():
            continue
        items.append(
            {
                "label": label,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return items


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Dict[str, object] | List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
