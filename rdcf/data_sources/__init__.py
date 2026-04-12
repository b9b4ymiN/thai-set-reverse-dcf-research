"""Datasource adapters for Thai reverse DCF workflows."""

from .set_site_validation import build_validation_reference, build_validation_references
from .yahoo_source import (
    DEFAULT_REQUIRED_FIELDS,
    DEFAULT_SNAPSHOT_FIELDS,
    YahooFinanceSource,
    build_datasource_quality_report,
    build_reverse_dcf_exclusion_report,
)
from .stockanalysis_source import (
    CachedYahooBundleSource,
    StockAnalysisHybridSource,
)

__all__ = [
    "DEFAULT_REQUIRED_FIELDS",
    "DEFAULT_SNAPSHOT_FIELDS",
    "YahooFinanceSource",
    "CachedYahooBundleSource",
    "StockAnalysisHybridSource",
    "build_datasource_quality_report",
    "build_reverse_dcf_exclusion_report",
    "build_validation_reference",
    "build_validation_references",
]
