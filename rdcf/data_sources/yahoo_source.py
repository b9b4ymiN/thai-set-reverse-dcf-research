from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import pandas as pd
import yfinance as yf


DEFAULT_REQUIRED_FIELDS = ('Current_Price', 'Market_Cap', 'FCF', 'WACC')
DEFAULT_SNAPSHOT_FIELDS = (
    'Ticker', 'Company_Name', 'Sector', 'Industry', 'Current_Price', 'Market_Cap',
    'EPS', 'PE_Ratio', 'PB_Ratio', 'EV_EBITDA', 'Revenue', 'Revenue_Growth', 'EBIT',
    'FCF', 'Total_Debt', 'Total_Cash', 'Debt_to_Equity', 'Current_Ratio',
    'Profit_Margin', 'Operating_Margin', 'ROE', 'ROA', 'Beta', 'Cost_of_Equity',
    'Cost_of_Debt', 'WACC', 'Dividend_Yield', 'Payout_Ratio', 'Earnings_Growth',
    'Fetched_Date'
)
STATEMENT_OBSERVATION_FIELDS = (
    'Ticker', 'Period_Type', 'Statement_Date', 'Availability_Date', 'Reporting_Lag_Days',
    'Revenue', 'EBIT', 'Interest_Expense', 'FCF', 'Total_Debt', 'Total_Cash', 'Net_Debt',
    'Shares_Issued', 'Diluted_Average_Shares', 'Revenue_Growth'
)


@dataclass
class YahooFinanceSource:
    ticker_factory: Callable[[str], object] = yf.Ticker
    now_factory: Callable[[], datetime] = datetime.now

    def fetch_stock_data(self, ticker: str) -> Optional[Dict[str, object]]:
        try:
            stock = self.ticker_factory(ticker)
            return self._build_snapshot_row(ticker, stock)
        except Exception:
            return None

    def fetch_ticker_bundle(self, ticker: str, reporting_lag_days: int = 45) -> Dict[str, object]:
        try:
            stock = self.ticker_factory(ticker)
            snapshot = self._build_snapshot_row(ticker, stock)
            observations = self._build_statement_observations(ticker, stock, reporting_lag_days)
            return {'snapshot': snapshot, 'observations': observations}
        except Exception:
            return {'snapshot': None, 'observations': pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS)}

    def fetch_all_stocks(self, tickers: Iterable[str]) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        for ticker in tickers:
            stock_data = self.fetch_stock_data(ticker)
            if stock_data:
                rows.append(stock_data)
        df = pd.DataFrame(rows)
        if not df.empty:
            missing_cols = [column for column in DEFAULT_SNAPSHOT_FIELDS if column not in df.columns]
            for column in missing_cols:
                df[column] = 0
            df = df[list(DEFAULT_SNAPSHOT_FIELDS)]
        return df

    def _build_snapshot_row(self, ticker: str, stock: object) -> Dict[str, object]:
        info = getattr(stock, 'info', {}) or {}
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        market_cap = info.get('marketCap') or 0
        eps = info.get('trailingEps') or info.get('epsTrailingTwelveMonths') or 0
        pe_ratio = info.get('trailingPE') or 0
        pb_ratio = info.get('priceToBook') or 0
        ev_ebitda = info.get('enterpriseToEbitda') or 0
        total_debt = info.get('totalDebt') or 0
        total_cash = info.get('totalCash') or 0
        debt_to_equity = info.get('debtToEquity') or 0
        current_ratio = info.get('currentRatio') or 0
        profit_margin = info.get('profitMargins') or 0
        operating_margin = info.get('operatingMargins') or 0
        roe = info.get('returnOnEquity') or 0
        roa = info.get('returnOnAssets') or 0
        revenue_growth = info.get('revenueGrowth') or 0
        earnings_growth = info.get('earningsGrowth') or 0
        dividend_yield = info.get('dividendYield') or 0
        payout_ratio = info.get('payoutRatio') or 0

        income_stmt = self._safe_frame(getattr(stock, 'income_stmt', None))
        cash_flow = self._safe_frame(getattr(stock, 'cash_flow', None))
        fcf = self._extract_fcf(cash_flow)
        revenue = self._frame_value(income_stmt, 'Total Revenue')
        ebit = self._frame_value(income_stmt, 'EBIT')

        risk_free_rate = 0.035
        beta = info.get('beta') or 1.0
        market_risk_premium = 0.06
        cost_of_equity = risk_free_rate + beta * market_risk_premium
        interest_expense = self._frame_value(income_stmt, 'Interest Expense')
        cost_of_debt = (interest_expense / total_debt) if total_debt > 0 else 0.05
        tax_rate = 0.20
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
        equity_value = market_cap
        debt_value = total_debt
        total_capital = equity_value + debt_value
        if total_capital > 0:
            equity_weight = equity_value / total_capital
            debt_weight = debt_value / total_capital
            wacc = (cost_of_equity * equity_weight) + (after_tax_cost_of_debt * debt_weight)
        else:
            wacc = cost_of_equity

        return {
            'Ticker': ticker,
            'Company_Name': info.get('longName', ticker),
            'Sector': info.get('sector', 'N/A'),
            'Industry': info.get('industry', 'N/A'),
            'Current_Price': current_price,
            'Market_Cap': market_cap,
            'EPS': eps,
            'PE_Ratio': pe_ratio,
            'PB_Ratio': pb_ratio,
            'EV_EBITDA': ev_ebitda,
            'Revenue': revenue,
            'Revenue_Growth': revenue_growth,
            'EBIT': ebit,
            'FCF': fcf,
            'Total_Debt': total_debt,
            'Total_Cash': total_cash,
            'Debt_to_Equity': debt_to_equity,
            'Current_Ratio': current_ratio,
            'Profit_Margin': profit_margin,
            'Operating_Margin': operating_margin,
            'ROE': roe,
            'ROA': roa,
            'Beta': beta,
            'Cost_of_Equity': cost_of_equity,
            'Cost_of_Debt': cost_of_debt,
            'WACC': wacc,
            'Dividend_Yield': dividend_yield,
            'Payout_Ratio': payout_ratio,
            'Earnings_Growth': earnings_growth,
            'Fetched_Date': self.now_factory().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def _build_statement_observations(self, ticker: str, stock: object, reporting_lag_days: int) -> pd.DataFrame:
        quarterly = self._statement_observations_from_frames(
            ticker=ticker,
            income_stmt=self._safe_frame(getattr(stock, 'quarterly_income_stmt', None)),
            cash_flow=self._safe_frame(getattr(stock, 'quarterly_cash_flow', None)),
            balance_sheet=self._safe_frame(getattr(stock, 'quarterly_balance_sheet', None)),
            period_type='quarterly',
            reporting_lag_days=reporting_lag_days,
        )
        annual = self._statement_observations_from_frames(
            ticker=ticker,
            income_stmt=self._safe_frame(getattr(stock, 'income_stmt', None)),
            cash_flow=self._safe_frame(getattr(stock, 'cash_flow', None)),
            balance_sheet=self._safe_frame(getattr(stock, 'balance_sheet', None)),
            period_type='annual',
            reporting_lag_days=reporting_lag_days,
        )
        observations = pd.concat([quarterly, annual], ignore_index=True, sort=False)
        if observations.empty:
            return pd.DataFrame(columns=STATEMENT_OBSERVATION_FIELDS)

        observations = observations.sort_values(['Ticker', 'Period_Type', 'Statement_Date']).reset_index(drop=True)
        observations['Revenue_Growth'] = observations.groupby(['Ticker', 'Period_Type'])['Revenue'].transform(self._compute_revenue_growth)
        for column in STATEMENT_OBSERVATION_FIELDS:
            if column not in observations.columns:
                observations[column] = pd.NA
        return observations[list(STATEMENT_OBSERVATION_FIELDS)]

    def _statement_observations_from_frames(
        self,
        ticker: str,
        income_stmt: pd.DataFrame,
        cash_flow: pd.DataFrame,
        balance_sheet: pd.DataFrame,
        period_type: str,
        reporting_lag_days: int,
    ) -> pd.DataFrame:
        statement_dates = self._sorted_statement_dates(income_stmt, cash_flow, balance_sheet)
        rows = []
        for statement_date in statement_dates:
            total_debt = self._frame_column_value(balance_sheet, 'Total Debt', statement_date)
            total_cash = self._frame_column_value(balance_sheet, 'Cash And Cash Equivalents', statement_date)
            if total_cash == 0:
                total_cash = self._frame_column_value(balance_sheet, 'Cash Cash Equivalents And Short Term Investments', statement_date)
            shares_issued = self._frame_column_value(balance_sheet, 'Share Issued', statement_date)
            diluted_avg_shares = self._frame_column_value(income_stmt, 'Diluted Average Shares', statement_date)
            rows.append({
                'Ticker': ticker,
                'Period_Type': period_type,
                'Statement_Date': statement_date.date().isoformat(),
                'Availability_Date': (statement_date + pd.to_timedelta(reporting_lag_days, unit='D')).date().isoformat(),
                'Reporting_Lag_Days': reporting_lag_days,
                'Revenue': self._frame_column_value(income_stmt, 'Total Revenue', statement_date),
                'EBIT': self._frame_column_value(income_stmt, 'EBIT', statement_date),
                'Interest_Expense': self._frame_column_value(income_stmt, 'Interest Expense', statement_date),
                'FCF': self._extract_fcf_for_date(cash_flow, statement_date),
                'Total_Debt': total_debt,
                'Total_Cash': total_cash,
                'Net_Debt': total_debt - total_cash,
                'Shares_Issued': shares_issued,
                'Diluted_Average_Shares': diluted_avg_shares,
            })
        return pd.DataFrame(rows)

    @staticmethod
    def _sorted_statement_dates(*frames: pd.DataFrame) -> List[pd.Timestamp]:
        dates = set()
        for frame in frames:
            if frame is not None and not frame.empty:
                for column in frame.columns:
                    dates.add(pd.Timestamp(column))
        return sorted(dates)

    @staticmethod
    def _compute_revenue_growth(series: pd.Series) -> pd.Series:
        prior = series.shift(1)
        growth = (series / prior) - 1
        growth = growth.where(prior.notna() & (prior != 0))
        return growth

    @staticmethod
    def _safe_frame(frame: Optional[pd.DataFrame]) -> pd.DataFrame:
        if frame is None:
            return pd.DataFrame()
        return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame(frame)

    @staticmethod
    def _frame_value(frame: pd.DataFrame, row_name: str, default: float = 0.0) -> float:
        if frame.empty or row_name not in frame.index:
            return default
        try:
            value = frame.loc[row_name].iloc[0]
            return float(value) if pd.notna(value) else default
        except Exception:
            return default

    @staticmethod
    def _frame_column_value(frame: pd.DataFrame, row_name: str, column: pd.Timestamp, default: float = 0.0) -> float:
        if frame.empty or row_name not in frame.index or column not in frame.columns:
            return default
        try:
            value = frame.loc[row_name, column]
            return float(value) if pd.notna(value) else default
        except Exception:
            return default

    def _extract_fcf(self, cash_flow: pd.DataFrame) -> float:
        if cash_flow.empty:
            return 0.0
        if 'Free Cash Flow' in cash_flow.index:
            return self._frame_value(cash_flow, 'Free Cash Flow')
        ocf = self._frame_value(cash_flow, 'Operating Cash Flow')
        capex = self._frame_value(cash_flow, 'Capital Expenditure')
        return ocf - abs(capex)

    def _extract_fcf_for_date(self, cash_flow: pd.DataFrame, column: pd.Timestamp) -> float:
        if cash_flow.empty:
            return 0.0
        if 'Free Cash Flow' in cash_flow.index:
            return self._frame_column_value(cash_flow, 'Free Cash Flow', column)
        ocf = self._frame_column_value(cash_flow, 'Operating Cash Flow', column)
        capex = self._frame_column_value(cash_flow, 'Capital Expenditure', column)
        return ocf - abs(capex)


def build_datasource_quality_report(
    df: pd.DataFrame,
    required_fields: Sequence[str] = DEFAULT_REQUIRED_FIELDS,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['Field', 'Missing_Count', 'Coverage_Pct', 'Zero_Count'])

    rows = []
    total_rows = len(df)
    for field in df.columns:
        series = df[field]
        missing_count = int(series.isna().sum())
        zero_count = int((series == 0).sum()) if pd.api.types.is_numeric_dtype(series) else 0
        coverage_pct = ((total_rows - missing_count) / total_rows) * 100 if total_rows else 0.0
        is_required = field in required_fields
        rows.append({
            'Field': field,
            'Missing_Count': missing_count,
            'Coverage_Pct': round(coverage_pct, 2),
            'Zero_Count': zero_count,
            'Required_For_Reverse_DCF': is_required,
        })
    return pd.DataFrame(rows).sort_values(['Required_For_Reverse_DCF', 'Coverage_Pct', 'Field'], ascending=[False, True, True]).reset_index(drop=True)


def build_reverse_dcf_exclusion_report(
    df: pd.DataFrame,
    required_fields: Sequence[str] = DEFAULT_REQUIRED_FIELDS,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=['Ticker', 'Passes_Reverse_DCF_Filter', 'Exclusion_Reasons'])

    reports = []
    for _, row in df.iterrows():
        reasons = []
        for field in required_fields:
            value = row.get(field, 0)
            if pd.isna(value) or value <= 0:
                reasons.append(f'{field}<=0_or_missing')
        reports.append({
            'Ticker': row.get('Ticker', 'UNKNOWN'),
            'Passes_Reverse_DCF_Filter': not reasons,
            'Exclusion_Reasons': ';'.join(reasons) if reasons else 'PASS',
        })
    return pd.DataFrame(reports)
