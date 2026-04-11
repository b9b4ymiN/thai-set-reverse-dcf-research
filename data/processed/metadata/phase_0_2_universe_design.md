# Phase 0.2: Date-Versioned Universe Design

## Problem Statement

Current backtest has **13% survivorship bias** - excludes 13 stocks with no data.

## Root Cause

```python
# Current approach (src/pipeline/backtest.py)
self.universe_tickers = sorted(set(self.observation_lookup) | set(self.price_lookup))
# → Only stocks WITH data are included
# → Delisted/missing stocks AUTOMATICALLY excluded
# → Creates survivorship bias by design
```

## Solution: Point-in-Time Universe Reconstruction

### Core Principle

> "Universe at any historical date should contain ONLY stocks that existed on that date"  
> — Damodaran's backtesting principle #2 (Universe Construction)

### Methodology

#### 1. Historical Universe Discovery

```python
def get_universe_at_date(target_date):
    """
    Returns SET100 composition as of target_date
    
    Sources (priority order):
    1. Historical SET100 announcements (Stock Exchange of Thailand)
    2. Historical index constituent files
    3. News archives of index changes
    """
    universe = []
    
    # Method A: Check if stock WAS in SET100 on target_date
    for ticker in ALL_THAI_STOCKS:
        listed_date = get_listing_date(ticker)
        delisted_date = get_delisted_date(ticker)
        
        # Stock must exist on target_date
        if listed_date <= target_date <= delisted_date:
            # Check if it was IN SET100 on that date
            if was_in_set100_on_date(ticker, target_date):
                universe.append(ticker)
    
    return universe
```

#### 2. Data Availability Handling

For stocks IN universe but WITHOUT data:

```python
def handle_missing_data(ticker, target_date):
    """
    Damodaran principle: "Missing data ≠ exclusion from universe"
    
    Options:
    1. Mark as "excluded from this period's backtest" (transparent)
    2. Use proxy/peer data (advanced)
    3. Carry forward last available price (with lag warning)
    """
    if ticker in universe_but_no_data:
        # Record as data limitation, NOT universe exclusion
        backtest_log.append(f"{ticker}: In universe but no data on {target_date}")
        # Option 1: Skip this stock for THIS period only
        # Option 2: Use last observation (with decay factor)
```

#### 3. Universe Versioning

```python
class VersionedUniverse:
    """
    Manages point-in-time universe composition
    """
    
    def __init__(self):
        self.universe_versions = {}  # date → set of tickers
    
    def build_version(self, date):
        """Build universe for specific date"""
        if date not in self.universe_versions:
            self.universe_versions[date] = get_universe_at_date(date)
        return self.universe_versions[date]
    
    def get_universe_series(self, start_date, end_date, frequency='Q'):
        """
        Returns universe composition for each rebalancing period
        
        Example:
        2021-03-31: [DELTA.BK, PTT.BK, ..., INTUCH.BK]  # 100 stocks
        2021-06-30: [DELTA.BK, PTT.BK, ..., TRUE.BK]    # INTUCH delisted, TRUE added
        2021-09-30: [DELTA.BK, PTT.BK, ..., TRUE.BK]    # 100 stocks
        """
        periods = pd.date_range(start_date, end_date, freq=frequency)
        return {date: self.build_version(date) for date in periods}
```

## Implementation Requirements

### Data Sources Needed

1. **Historical SET100 Constituent Lists**
   - Source: Stock Exchange of Thailand (SET) announcements
   - Format: PDF/Excel files with effective dates
   - Coverage: 2021-2025 (quarterly rebalancing)

2. **Listing/Delisting Dates**
   - Source: SET company data
   - Fields: listing_date, delisting_date, delisting_reason

3. **Corporate Actions**
   - Mergers (e.g., TMB → TTBB)
   - Spin-offs
   - Name changes

### Feasibility Assessment (Thai Free Data)

| Requirement | Feasibility | Source | Notes |
|-------------|-------------|---------|-------|
| Historical SET100 lists | ⚠️ PARTIAL | SET website | PDF archives, may need manual extraction |
| Listing dates | ✅ FULL | Yahoo Finance | Available |
| Delisting dates | ⚠️ PARTIAL | SET announcements | Need to search news archives |
| Corporate actions | ❌ LIMITED | None free | Major limitation |

## Recommended Approach

### Option A: Pragmatic Compromise (Recommended)

```python
# Use CURRENT SET100 as proxy for historical universe
# BUT explicitly document limitations

UNIVERSE_APPROXIMATION = {
    "period": "2021-2025",
    "method": "Static SET100 (current) as proxy",
    "bias_estimate": "~13% (13 excluded stocks)",
    "justification": """
        Historical constituent data not freely available.
        Using current SET100 as approximation.
        Limitation: Delisted stocks excluded, creating survivorship bias.
        Impact: Returns may be overstated by ~2-5%.
    """
}

# Implementation:
# 1. Use 87 scraped stocks as primary universe
# 2. Document 13 excluded stocks clearly
# 3. Add disclaimer to all backtest results
# 4. Phase 2 of research: Extract principles for handling this limitation
```

### Option B: Full Reconstruction (Ideal but Expensive)

```python
# Manually reconstruct historical universe

EFFORT_REQUIRED = "20-30 hours"

STEPS = [
    "1. Search SET archives for quarterly rebalancing announcements",
    "2. Extract constituent lists for 2021-2025 (20 quarters)",
    "3. Build date-versioned universe database",
    "4. Implement versioned universe in backtest.py",
    "5. Validate against historical records"
]

BENEFIT = "Eliminates survivorship bias completely"
COST = "20-30 hours manual work"
```

## Decision Matrix (Updated for Free Data Constraints)

```
IF historical constituent data freely available THEN
    Option B: Full reconstruction (ideal)
ELSE IF acceptable 13% bias with documentation THEN
    Option A: Pragmatic compromise (recommended)
    Document limitation clearly in backtest results
    Focus Phase 2 research on bias-correction principles
END IF
```

## Immediate Next Steps

1. ✅ Check if historical SET100 data available (DOING)
2. Estimate effort for manual reconstruction
3. Make final decision: Option A or B
4. Document decision with rationale
5. Proceed to Phase 1 (Content Inventory) if Option A
   OR Execute reconstruction if Option B

---

**Phase 0.2 Status**: In Progress - Awaiting feasibility check

