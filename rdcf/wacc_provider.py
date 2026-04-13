import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
from pathlib import Path
import datetime

class DamodaranWACCProvider:
    """
    Provides WACC calculations based on Damodaran NYU Stern methodology.
    Supports industry-level unlevered betas, country risk premiums for Thailand,
    and ICR-based default spreads for cost of debt.
    """

    # Industry Unlevered Beta Mapping (Emerging Markets, Jan 2026)
    # Source: docs/damodaran-stern-datasets-thai-set.md
    UNLEVERED_BETAS = {
        'Advertising Agencies': 0.70,
        'Airports & Air Services': 0.65,
        'Apparel Manufacturing': 0.75,
        'Auto Parts': 0.80,
        'Banks - Regional': 0.12, # Low unlevered beta for banks
        'Beverages - Non-Alcoholic': 0.55,
        'Building Products & Equipment': 0.70,
        'Capital Markets': 0.85,
        'Chemicals': 0.75,
        'Computer Hardware': 0.90,
        'Confectioners': 0.55,
        'Conglomerates': 0.65,
        'Credit Services': 0.80,
        'Department Stores': 0.60,
        'Drug Manufacturers - Specialty & Generic': 0.75,
        'Electrical Equipment & Parts': 0.80,
        'Electronic Components': 0.95,
        'Engineering & Construction': 0.40, # Often low unlevered
        'Entertainment': 0.85,
        'Farm Products': 0.60,
        'Grocery Stores': 0.50,
        'Home Improvement Retail': 0.62,
        'Industry': 0.70,
        'Insurance - Life': 0.15,
        'Lodging': 0.52,
        'Marine Shipping': 0.75,
        'Medical Care Facilities': 0.62,
        'Metal Fabrication': 0.75,
        'Oil & Gas E&P': 0.75,
        'Oil & Gas Integrated': 0.70,
        'Oil & Gas Refining & Marketing': 0.70,
        'Packaged Foods': 0.56,
        'Packaging & Containers': 0.56,
        'Railroads': 0.60,
        'Real Estate - Development': 0.39,
        'Real Estate - Diversified': 0.40,
        'Real Estate Services': 0.65,
        'Rental & Leasing Services': 0.65,
        'Resorts & Casinos': 0.80,
        'Specialty Chemicals': 0.80,
        'Specialty Retail': 0.70,
        'Telecom Services': 0.57,
        'Textile Manufacturing': 0.75,
        'Thermal Coal': 0.70,
        'Utilities - Independent Power Producers': 0.55,
        'Utilities - Regulated Electric': 0.45,
        'Utilities - Renewable': 0.60,
        'DEFAULT': 0.75
    }

    # Thai 10Y Bond Yields (Approximated history)
    THAI_10Y_YIELDS = {
        2016: 0.022,
        2017: 0.025,
        2018: 0.028,
        2019: 0.020,
        2020: 0.013,
        2021: 0.018,
        2022: 0.025,
        2023: 0.030,
        2024: 0.032,
        2025: 0.035,
        2026: 0.035
    }

    # Thailand Equity Risk Premium (CDS-based from doc)
    THAILAND_ERP = 0.0587

    # Tax Rate
    THAILAND_TAX_RATE = 0.20

    def __init__(self):
        data_dir = Path(__file__).parent / 'data'
        erp_path = data_dir / 'thailand_erp_history.csv'
        size_path = data_dir / 'size_premium_table.csv'
        self._erp_history = pd.read_csv(erp_path) if erp_path.exists() else None
        self._size_premium = pd.read_csv(size_path) if size_path.exists() else None

    def get_risk_free_rate(self, date: Any) -> float:
        """Get Thai 10Y bond yield for the given date."""
        if isinstance(date, str):
            year = pd.to_datetime(date).year
        elif hasattr(date, 'year'):
            year = date.year
        else:
            year = 2025
        
        return self.THAI_10Y_YIELDS.get(year, 0.035)

    def get_unlevered_beta(self, industry: str) -> float:
        """Get industry unlevered beta."""
        return self.UNLEVERED_BETAS.get(industry, self.UNLEVERED_BETAS['DEFAULT'])

    def get_default_spread(self, icr: float) -> float:
        """Get default spread based on Interest Coverage Ratio (ICR)."""
        if icr > 8.5: return 0.0085
        if icr > 6.5: return 0.0100
        if icr > 5.5: return 0.0110
        if icr > 4.25: return 0.0120
        if icr > 3.0: return 0.0150
        if icr > 2.5: return 0.0200
        if icr > 2.25: return 0.0300
        if icr > 2.0: return 0.0400
        if icr > 1.75: return 0.0450
        if icr > 1.5: return 0.0550
        if icr > 1.25: return 0.0650
        if icr > 0.8: return 0.0850
        if icr > 0.5: return 0.1000
        return 0.1500

    def calculate_wacc(self, 
                       industry: str, 
                       equity_value: float, 
                       total_debt: float, 
                       ebit: float, 
                       interest_expense: float,
                       date: Any = None) -> Dict[str, float]:
        """
        Calculate WACC according to Damodaran's principles.
        """
        rf = self.get_risk_free_rate(date)
        unlevered_beta = self.get_unlevered_beta(industry)
        
        # Levered Beta = Unlevered Beta * (1 + (1 - tax) * D/E)
        de_ratio = total_debt / equity_value if equity_value > 0 else 0
        levered_beta = unlevered_beta * (1 + (1 - self.THAILAND_TAX_RATE) * de_ratio)
        
        # Cost of Equity (Ke) = Rf + Beta * ERP
        cost_of_equity = rf + levered_beta * self.THAILAND_ERP
        
        # Cost of Debt (Rd) = Rf + Default Spread
        icr = ebit / abs(interest_expense) if interest_expense != 0 else 999
        if icr < 0: icr = 0 # Distressed
        
        default_spread = self.get_default_spread(icr)
        cost_of_debt = rf + default_spread
        
        # Weights
        total_capital = equity_value + total_debt
        if total_capital > 0:
            we = equity_value / total_capital
            wd = total_debt / total_capital
            
            wacc = (cost_of_equity * we) + (cost_of_debt * (1 - self.THAILAND_TAX_RATE) * wd)
        else:
            wacc = cost_of_equity
            
        return {
            'wacc': wacc,
            'cost_of_equity': cost_of_equity,
            'cost_of_debt': cost_of_debt,
            'levered_beta': levered_beta,
            'unlevered_beta': unlevered_beta,
            'risk_free_rate': rf,
            'icr': icr
        }

    # ------------------------------------------------------------------
    # Dynamic ERP (time-varying, with 1-year lag to avoid lookahead)
    # Source: Damodaran country risk premium datasets (ctryprem*.xls/xlsx)
    # Methodology: Damodaran, Investment Valuation Ch.7 (ERP estimation)
    # ------------------------------------------------------------------

    def get_dynamic_erp(self, date: Any, mode: str = 'cds') -> float:
        """Return Thailand ERP for the given date with 1-year lag (no lookahead).

        For any rebalance date in year Y, returns ERP from year Y-1.
        This ensures no future information leaks into the backtest.

        Args:
            date: The rebalance date.
            mode: 'cds' for CDS-based ERP or 'rating' for rating-based ERP.

        Returns:
            Thailand ERP as a decimal (e.g. 0.0587).
        """
        if self._erp_history is None:
            return self.THAILAND_ERP

        if isinstance(date, str):
            year = pd.to_datetime(date).year
        elif hasattr(date, 'year'):
            year = date.year
        else:
            year = 2025

        lagged_year = year - 1  # No lookahead: use prior year's ERP
        row = self._erp_history[self._erp_history['year'] == lagged_year]

        if row.empty:
            return self.THAILAND_ERP  # Fallback to current snapshot

        col = 'erp_cds' if mode == 'cds' else 'erp_rating'
        return float(row[col].iloc[0])

    # ------------------------------------------------------------------
    # Size Premium (Damodaran small-cap premium for emerging markets)
    # Source: Damodaran size premium tables (emerging markets, Jan 2026)
    # Methodology: Damodaran, Investment Valuation Ch.8 (small-cap premium)
    # ------------------------------------------------------------------

    def get_size_premium(self, market_cap_thb: float) -> float:
        """Return size premium based on market cap (in THB).

        Small-cap stocks earn a premium over large-cap due to higher risk.
        Uses trailing market cap = entry price * current shares outstanding.

        Args:
            market_cap_thb: Market capitalization in THB (not billions).

        Returns:
            Size premium as a decimal (e.g. 0.040 for micro-cap).
        """
        if self._size_premium is None:
            return 0.0

        market_cap_b = market_cap_thb / 1e9  # Convert to billions

        for _, row in self._size_premium.iterrows():
            if market_cap_b < row['market_cap_ceil_thb_b']:
                return float(row['size_premium'])

        return 0.0  # Mega-cap: no size premium

    # ------------------------------------------------------------------
    # Blended Beta (regression + fundamental bottom-up blend)
    # Source: Damodaran betaemerg.xls (Jan 2026, 96 emerging market industries)
    # Methodology: Damodaran, Investment Valuation Ch.7 (beta estimation);
    #              Damodaran on Valuation Ch.5 (bottom-up beta)
    # ------------------------------------------------------------------

    def get_blended_beta(self, ticker: str, industry: str, d_e_ratio: float,
                         price_lookup: Dict, date: Any,
                         blend_weight: float = 0.5,
                         benchmark_df: 'pd.DataFrame' = None) -> float:
        """Return blended beta = w * regression_beta + (1-w) * fundamental_beta.

        Regression beta: 2-year weekly returns vs SET Index (Damodaran market model).
        Fundamental beta: industry unlevered beta relevered with firm D/E.
        Fallback: If regression std error > 0.5 or < 52 weeks of data,
        use 100% fundamental beta.
        Result is clamped to [0.1, 3.0] to prevent degenerate values.

        Args:
            ticker: Stock ticker symbol.
            industry: Industry classification string.
            d_e_ratio: Debt-to-equity ratio for relevering.
            price_lookup: Dict mapping ticker -> DataFrame of price history.
            date: The rebalance date (cutoff for lookahead guard).
            blend_weight: Weight on regression beta (0.0-1.0, default 0.5).
            benchmark_df: DataFrame of SET Index price history (Date, Close columns).

        Returns:
            Blended levered beta, clamped to [0.1, 3.0].
        """
        unlevered = self.get_unlevered_beta(industry)
        levered_fundamental = unlevered * (1 + (1 - self.THAILAND_TAX_RATE) * d_e_ratio)

        regression_beta = self._compute_regression_beta(ticker, price_lookup, date, benchmark_df)

        if regression_beta is None:
            return levered_fundamental  # 100% fundamental fallback

        blended = blend_weight * regression_beta + (1 - blend_weight) * levered_fundamental
        # Boundary guard: clamp beta to [0.1, 3.0]
        # (Damodaran, Investment Valuation Ch.7: extreme betas are estimation artifacts)
        return max(0.1, min(3.0, blended))

    def _compute_regression_beta(self, ticker: str, price_lookup: Dict,
                                  date: Any,
                                  benchmark_df: 'pd.DataFrame' = None) -> Optional[float]:
        """Compute 2-year weekly regression beta vs SET Index (market model).

        Implements the Damodaran market model:
            β = Cov(R_stock, R_market) / Var(R_market)

        where R_market = weekly returns of SET Index from benchmark_history.csv.

        NO-LOOKAHEAD GUARD: Only uses price data on or before `date`.
        Returns None if insufficient data or high std error.

        Reference: Damodaran, Investment Valuation 3rd ed., Ch.7 (beta estimation);
                  Damodaran on Valuation 2nd ed., Ch.5 (bottom-up beta).
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)
        elif not hasattr(date, 'year'):
            date = pd.Timestamp(date)

        # --- Stock weekly returns (no lookahead) ---
        frame = price_lookup.get(ticker)
        if frame is None or frame.empty:
            return None

        frame = frame.copy()
        frame['Date'] = pd.to_datetime(frame['Date'])
        cutoff = date
        eligible = frame[frame['Date'] <= cutoff].sort_values('Date')

        if len(eligible) < 52:
            return None

        two_years_ago = cutoff - pd.DateOffset(years=2)
        eligible = eligible[eligible['Date'] >= two_years_ago]

        if len(eligible) < 52:
            return None

        eligible = eligible.set_index('Date')
        stock_weekly = eligible.resample('W').last().dropna(subset=['Close'])
        if len(stock_weekly) < 48:
            return None
        stock_returns = stock_weekly['Close'].astype(float).pct_change().dropna()
        if len(stock_returns) < 40:
            return None

        # --- Benchmark (SET Index) weekly returns (no lookahead) ---
        if benchmark_df is None or benchmark_df.empty:
            return None

        bench = benchmark_df.copy()
        bench['Date'] = pd.to_datetime(bench['Date'])
        bench = bench[bench['Date'] <= cutoff].sort_values('Date')
        bench = bench[bench['Date'] >= two_years_ago]

        if len(bench) < 52:
            return None

        bench = bench.set_index('Date')
        bench_weekly = bench.resample('W').last().dropna(subset=['Close'])
        if len(bench_weekly) < 48:
            return None
        bench_returns = bench_weekly['Close'].astype(float).pct_change().dropna()
        if len(bench_returns) < 40:
            return None

        # --- Align stock and benchmark returns on same dates ---
        stock_returns.index = stock_returns.index.normalize()
        bench_returns.index = bench_returns.index.normalize()
        aligned = pd.DataFrame({
            'stock': stock_returns,
            'market': bench_returns,
        }).dropna()

        if len(aligned) < 40:
            return None

        # --- Market model: β = Cov(R_stock, R_market) / Var(R_market) ---
        # This is the standard OLS regression beta (Damodaran, Investment Valuation Ch.7)
        cov_matrix = np.cov(aligned['stock'].values, aligned['market'].values, ddof=1)
        cov_sm = cov_matrix[0, 1]
        var_m = cov_matrix[1, 1]

        if var_m <= 1e-12:
            return None

        beta_est = cov_sm / var_m

        # Std error check: reject if estimation error too high
        n = len(aligned)
        residuals = aligned['stock'].values - (beta_est * aligned['market'].values)
        # Alpha (intercept) for proper residual calculation
        alpha = aligned['stock'].mean() - beta_est * aligned['market'].mean()
        residuals = aligned['stock'].values - (alpha + beta_est * aligned['market'].values)
        se_beta = np.sqrt(np.sum(residuals**2) / (n - 2)) / np.sqrt(np.sum((aligned['market'].values - aligned['market'].mean())**2))

        if se_beta > 0.5:
            return None  # High estimation error — fall back to fundamental beta

        # Blume adjustment: shrink raw beta toward 1.0
        # (Damodaran, Investment Valuation 3rd ed., Ch.7; Blume, 1971)
        # Rationale: raw regression betas tend to revert toward the mean (1.0) over time
        beta_est = 0.33 + 0.67 * beta_est

        # Clamp to reasonable range before blending
        beta_est = max(0.1, min(3.0, beta_est))
        return float(beta_est)

    # ------------------------------------------------------------------
    # ROIC — Return on Invested Capital (Damodaran EVA framework)
    # Source: Damodaran, Investment Valuation 3rd ed., Ch.31; Damodaran on Valuation Ch.9
    # Formula: ROIC = NOPAT / Invested_Capital = EBIT*(1-t) / (Debt + Equity - Cash)
    # Economic Value Added (EVA): ROIC > WACC => firm creates value
    # ------------------------------------------------------------------

    def calculate_roic(self, ebit: float, total_debt: float,
                       equity_value: float, cash: float = 0) -> float:
        """Return on Invested Capital (Damodaran, Investment Valuation Ch.31).

        ROIC measures how effectively a company uses its capital to generate profits.
        A firm creates value when ROIC > WACC (Economic Value Added).

        Args:
            ebit: Earnings Before Interest and Taxes.
            total_debt: Total debt outstanding.
            equity_value: Market value of equity (or book value if preferred).
            cash: Cash and cash equivalents (subtracted from invested capital).

        Returns:
            ROIC as a decimal (e.g. 0.15 for 15%).
        """
        nopat = ebit * (1 - self.THAILAND_TAX_RATE)
        invested_capital = total_debt + equity_value - cash
        if invested_capital <= 0:
            return 0.0
        return nopat / invested_capital

    # ------------------------------------------------------------------
    # Comprehensive WACC (configurable components)
    # ------------------------------------------------------------------

    def calculate_wacc_comprehensive(self,
                                      industry: str,
                                      equity_value: float,
                                      total_debt: float,
                                      ebit: float,
                                      interest_expense: float,
                                      date: Any = None,
                                      config: Optional[Dict] = None) -> Dict[str, float]:
        """Comprehensive WACC calculation with configurable components.

        Config keys:
            erp_mode: 'cds' or 'rating' (default: 'cds')
            include_size_premium: bool (default: False)
            beta_mode: 'fundamental_only' or 'balanced' (default: 'fundamental_only')
            blend_weight: float 0.0-1.0 (default: 0.5, weight on regression beta)
            ticker: str (required for balanced beta)
            price_lookup: dict (required for balanced beta)

        Returns dict with all WACC components plus metadata for audit trail.
        """
        cfg = config or {}
        erp_mode = cfg.get('erp_mode', 'cds')
        include_size = cfg.get('include_size_premium', False)
        beta_mode = cfg.get('beta_mode', 'fundamental_only')
        blend_weight = cfg.get('blend_weight', 0.5)

        rf = self.get_risk_free_rate(date)
        erp = self.get_dynamic_erp(date, mode=erp_mode)
        unlevered = self.get_unlevered_beta(industry)
        de_ratio = total_debt / equity_value if equity_value > 0 else 0

        if beta_mode == 'balanced' and cfg.get('price_lookup') and cfg.get('ticker'):
            levered_beta = self.get_blended_beta(
                cfg['ticker'], industry, de_ratio, cfg['price_lookup'],
                date, blend_weight=blend_weight,
                benchmark_df=cfg.get('benchmark_df'))
        else:
            levered_beta = unlevered * (1 + (1 - self.THAILAND_TAX_RATE) * de_ratio)

        cost_of_equity = rf + levered_beta * erp

        if include_size and equity_value > 0:
            size_prem = self.get_size_premium(equity_value)
            cost_of_equity += size_prem
        else:
            size_prem = 0.0

        # Cost of Debt
        icr = ebit / abs(interest_expense) if interest_expense != 0 else 999
        if icr < 0:
            icr = 0
        default_spread = self.get_default_spread(icr)
        cost_of_debt = rf + default_spread

        # WACC
        total_capital = equity_value + total_debt
        if total_capital > 0:
            we = equity_value / total_capital
            wd = total_debt / total_capital
            wacc = (cost_of_equity * we) + (cost_of_debt * (1 - self.THAILAND_TAX_RATE) * wd)
        else:
            wacc = cost_of_equity

        # Determine ERP lag year
        if isinstance(date, str):
            erp_lag_year = pd.to_datetime(date).year - 1
        elif hasattr(date, 'year'):
            erp_lag_year = date.year - 1
        else:
            erp_lag_year = 2024

        return {
            'wacc': wacc,
            'cost_of_equity': cost_of_equity,
            'cost_of_debt': cost_of_debt,
            'levered_beta': levered_beta,
            'unlevered_beta': unlevered,
            'risk_free_rate': rf,
            'erp_used': erp,
            'erp_mode': erp_mode,
            'size_premium': size_prem,
            'beta_mode': beta_mode,
            'icr': icr,
            'erp_lag_year': erp_lag_year,
        }

if __name__ == "__main__":
    # Test
    provider = DamodaranWACCProvider()
    res = provider.calculate_wacc('Banks - Regional', 1000, 200, 100, 10, '2024-01-01')
    print(res)
