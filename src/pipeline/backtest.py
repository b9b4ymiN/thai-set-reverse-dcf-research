from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from reverse_dcf_model import solve_reverse_dcf


DEFAULT_HORIZONS = (3, 6, 12)


@dataclass
class ReverseDCFBacktester:
    snapshot_path: str = 'research_data/latest/fundamentals_snapshot.csv'
    observations_path: str = 'research_data/latest/fundamental_observations.csv'
    price_history_path: str = 'research_data/latest/price_history.csv'
    benchmark_history_path: str = 'research_data/latest/benchmark_history.csv'
    signal_solver: Callable[..., Tuple[float, dict]] = solve_reverse_dcf
    default_wacc: float = 0.08
    wacc_mode: str = 'fixed'

    def __post_init__(self) -> None:
        self.snapshot = pd.read_csv(self.snapshot_path)
        self.observations = pd.read_csv(self.observations_path)
        self.prices = pd.read_csv(self.price_history_path)
        self.benchmark = pd.read_csv(self.benchmark_history_path)

        self.observations['Statement_Date'] = pd.to_datetime(self.observations['Statement_Date'])
        self.observations['Availability_Date'] = pd.to_datetime(self.observations['Availability_Date'])
        self.prices['Date'] = pd.to_datetime(self.prices['Date'])
        self.benchmark['Date'] = pd.to_datetime(self.benchmark['Date'])

        self.observations = self.observations.sort_values(['Ticker', 'Availability_Date', 'Statement_Date'])
        self.prices = self.prices.sort_values(['Ticker', 'Date'])
        self.benchmark = self.benchmark.sort_values('Date')

        self.price_lookup = {
            ticker: frame.reset_index(drop=True)
            for ticker, frame in self.prices.groupby('Ticker', sort=False)
        }
        self.observation_lookup = {
            ticker: frame.reset_index(drop=True)
            for ticker, frame in self.observations.groupby('Ticker', sort=False)
        }
        self.snapshot_lookup = self.snapshot.set_index('Ticker').to_dict('index') if not self.snapshot.empty else {}
        self.universe_tickers = sorted(set(self.observation_lookup) | set(self.price_lookup))

    def run(
        self,
        output_dir: str = 'research_data/latest/backtest',
        horizons: Sequence[int] = DEFAULT_HORIZONS,
        top_n: int = 10,
        rebalance_frequency: str = 'Q',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, object]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        rebalance_dates = self._build_rebalance_dates(rebalance_frequency, start_date, end_date)
        signal_rows: List[Dict[str, object]] = []
        holding_rows: List[Dict[str, object]] = []
        exclusion_rows: List[Dict[str, object]] = []
        audit_rows: List[Dict[str, object]] = []
        previous_portfolio: List[str] = []

        for rebalance_date in rebalance_dates:
            cross_section, exclusions = self._build_cross_section(rebalance_date)
            if cross_section.empty:
                continue
            universe_count = len(self.universe_tickers)
            excluded_count = len(exclusions)
            ranked = cross_section.sort_values('Signal_Score', ascending=False).reset_index(drop=True)
            ranked['Rebalance_Date'] = rebalance_date.date().isoformat()
            ranked['Universe_Count'] = universe_count
            ranked['Excluded_Count'] = excluded_count
            signal_rows.extend(ranked.to_dict('records'))
            if not exclusions.empty:
                exclusions = exclusions.copy()
                exclusions['Rebalance_Date'] = rebalance_date.date().isoformat()
                exclusions['Universe_Count'] = universe_count
                exclusion_rows.extend(exclusions.to_dict('records'))
            if not audit_rows:
                audit_rows = ranked.head(min(10, len(ranked))).to_dict('records')

            portfolio = ranked.head(min(top_n, len(ranked))).copy()
            turnover = self._calculate_turnover(previous_portfolio, portfolio['Ticker'].tolist())
            previous_portfolio = portfolio['Ticker'].tolist()
            for horizon in horizons:
                portfolio_holding, benchmark_return = self._evaluate_portfolio_horizon(portfolio, rebalance_date, horizon)
                if portfolio_holding.empty:
                    continue
                portfolio_return = portfolio_holding['Forward_Return'].mean()
                holding_rows.append({
                    'Rebalance_Date': rebalance_date.date().isoformat(),
                    'Horizon_Months': horizon,
                    'Top_N': len(portfolio_holding),
                    'Portfolio_Return': portfolio_return,
                    'Benchmark_Return': benchmark_return,
                    'Active_Return': portfolio_return - benchmark_return,
                    'Hit': portfolio_return > benchmark_return,
                    'Universe_Count': universe_count,
                    'Eligible_Count': len(ranked),
                    'Excluded_Count': excluded_count,
                    'Turnover': turnover,
                })
                portfolio_holding['Rebalance_Date'] = rebalance_date.date().isoformat()
                portfolio_holding['Horizon_Months'] = horizon
                portfolio_holding.to_csv(output_path / f"portfolio_{rebalance_date.date().isoformat()}_{horizon}m.csv", index=False, encoding='utf-8-sig')

        signals_df = pd.DataFrame(signal_rows)
        holdings_df = pd.DataFrame(holding_rows)
        exclusions_df = pd.DataFrame(exclusion_rows)
        audit_df = pd.DataFrame(audit_rows)
        summary_df = self._build_summary(holdings_df)
        manifest = self._build_manifest(
            signals_df=signals_df,
            holdings_df=holdings_df,
            exclusions_df=exclusions_df,
            summary_df=summary_df,
            output_path=output_path,
            horizons=horizons,
            top_n=top_n,
            rebalance_frequency=rebalance_frequency,
            wacc_mode=self.wacc_mode,
        )

        paths = {
            'signals': output_path / 'signals.csv',
            'exclusions': output_path / 'exclusions.csv',
            'portfolio_returns': output_path / 'portfolio_returns.csv',
            'summary': output_path / 'summary.csv',
            'audit_sample': output_path / 'audit_sample.csv',
            'audit_report': output_path / 'no_lookahead_audit.md',
            'report': output_path / 'report.md',
            'manifest': output_path / 'manifest.json',
        }
        signals_df.to_csv(paths['signals'], index=False, encoding='utf-8-sig')
        exclusions_df.to_csv(paths['exclusions'], index=False, encoding='utf-8-sig')
        holdings_df.to_csv(paths['portfolio_returns'], index=False, encoding='utf-8-sig')
        summary_df.to_csv(paths['summary'], index=False, encoding='utf-8-sig')
        audit_df.to_csv(paths['audit_sample'], index=False, encoding='utf-8-sig')
        paths['audit_report'].write_text(self._build_audit_report(audit_df, manifest), encoding='utf-8')
        paths['report'].write_text(self._build_report(summary_df, manifest), encoding='utf-8')
        paths['manifest'].write_text(json.dumps(manifest, indent=2), encoding='utf-8')

        return {
            'signals': len(signals_df),
            'portfolio_rows': len(holdings_df),
            'summary_rows': len(summary_df),
            'paths': {key: str(value) for key, value in paths.items()},
        }

    def _build_rebalance_dates(
        self,
        frequency: str,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[pd.Timestamp]:
        price_dates = pd.to_datetime(self.prices['Date'].dropna().unique())
        if len(price_dates) == 0:
            return []
        start = pd.Timestamp(start_date) if start_date else price_dates.min()
        end = pd.Timestamp(end_date) if end_date else price_dates.max()

        available_dates = pd.Series(sorted(price_dates))
        anchors = pd.date_range(start=start, end=end, freq=frequency)
        rebalance_dates: List[pd.Timestamp] = []
        for anchor in anchors:
            eligible = available_dates[available_dates >= anchor]
            if eligible.empty:
                continue
            rebalance_dates.append(pd.Timestamp(eligible.iloc[0]))
        return list(dict.fromkeys(rebalance_dates))

    def _build_cross_section(self, rebalance_date: pd.Timestamp) -> Tuple[pd.DataFrame, pd.DataFrame]:
        rows = []
        exclusions = []
        for ticker in self.universe_tickers:
            observation = self._latest_available_observation(ticker, rebalance_date)
            if observation is None:
                exclusions.append({'Ticker': ticker, 'Exclusion_Reason': 'no_available_observation'})
                continue
            price_info = self._price_info_on_or_before(ticker, rebalance_date)
            if price_info is None:
                exclusions.append({'Ticker': ticker, 'Exclusion_Reason': 'no_price_on_or_before'})
                continue
            price, price_date = price_info
            if price <= 0:
                exclusions.append({'Ticker': ticker, 'Exclusion_Reason': 'non_positive_price'})
                continue
            row, reason = self._score_observation(ticker, observation, price, price_date, rebalance_date)
            if row is not None:
                rows.append(row)
            else:
                exclusions.append({'Ticker': ticker, 'Exclusion_Reason': reason or 'signal_rejected'})
        return pd.DataFrame(rows), pd.DataFrame(exclusions)

    def _latest_available_observation(self, ticker: str, rebalance_date: pd.Timestamp) -> Optional[pd.Series]:
        frame = self.observation_lookup.get(ticker)
        if frame is None or frame.empty:
            return None
        eligible = frame.loc[frame['Availability_Date'] <= rebalance_date].copy()
        if eligible.empty:
            return None
        eligible = eligible.sort_values(['Availability_Date', 'Statement_Date'])
        return eligible.iloc[-1]

    def _price_info_on_or_before(self, ticker: str, target_date: pd.Timestamp) -> Optional[Tuple[float, pd.Timestamp]]:
        frame = self.price_lookup.get(ticker)
        if frame is None or frame.empty:
            return None
        eligible = frame.loc[frame['Date'] <= target_date]
        if eligible.empty:
            return None
        row = eligible.iloc[-1]
        price = float(row['Adj Close'] if pd.notna(row['Adj Close']) else row['Close'])
        return price, pd.Timestamp(row['Date'])

    def _benchmark_return(self, start_date: pd.Timestamp, horizon_months: int) -> Optional[float]:
        benchmark_start = self._series_price_on_or_before(self.benchmark, start_date)
        benchmark_end = self._series_price_on_or_before(self.benchmark, start_date + pd.DateOffset(months=horizon_months))
        if benchmark_start is None or benchmark_end is None or benchmark_start <= 0:
            return None
        return (benchmark_end / benchmark_start) - 1

    @staticmethod
    def _series_price_on_or_before(frame: pd.DataFrame, target_date: pd.Timestamp) -> Optional[float]:
        eligible = frame.loc[frame['Date'] <= target_date]
        if eligible.empty:
            return None
        row = eligible.iloc[-1]
        return float(row['Adj Close'] if pd.notna(row['Adj Close']) else row['Close'])

    def _score_observation(
        self,
        ticker: str,
        observation: pd.Series,
        price: float,
        price_date: pd.Timestamp,
        rebalance_date: pd.Timestamp,
    ) -> Tuple[Optional[Dict[str, object]], Optional[str]]:
        shares = observation.get('Diluted_Average_Shares') or observation.get('Shares_Issued')
        if pd.isna(shares) or shares is None or shares <= 0:
            return None, 'invalid_shares'
        fcf = observation.get('FCF', 0)
        if pd.isna(fcf) or fcf <= 0:
            return None, 'invalid_fcf'
        wacc = self._resolve_wacc(ticker)
        net_debt = observation.get('Net_Debt', 0) or 0
        implied_growth, details = self.signal_solver(
            base_fcf=float(fcf),
            wacc=float(wacc),
            current_price=float(price),
            shares_outstanding=float(shares),
            net_debt=float(net_debt),
        )
        if not details.get('converged', True):
            return None, 'no_convergence'
        actual_growth = observation.get('Revenue_Growth', 0)
        actual_growth = 0.0 if pd.isna(actual_growth) else float(actual_growth)
        signal_score = actual_growth - float(implied_growth)
        no_lookahead_pass = (
            pd.Timestamp(observation['Availability_Date']) <= rebalance_date and
            price_date <= rebalance_date and
            self.wacc_mode != 'snapshot'
        )
        return {
            'Ticker': ticker,
            'Price_Date': price_date.date().isoformat(),
            'Statement_Date': pd.Timestamp(observation['Statement_Date']).date().isoformat(),
            'Availability_Date': pd.Timestamp(observation['Availability_Date']).date().isoformat(),
            'Period_Type': observation['Period_Type'],
            'WACC_Mode': self.wacc_mode,
            'No_Lookahead_Pass': no_lookahead_pass,
            'Days_Since_Available': int((rebalance_date - pd.Timestamp(observation['Availability_Date'])).days),
            'Price': float(price),
            'FCF': float(fcf),
            'Shares': float(shares),
            'WACC': float(wacc),
            'Net_Debt': float(net_debt),
            'Actual_Revenue_Growth': actual_growth,
            'Implied_Growth_Rate': float(implied_growth),
            'Signal_Score': signal_score,
            'Intrinsic_Value': details.get('intrinsic_value', 0.0),
        }, None

    def _resolve_wacc(self, ticker: str) -> float:
        if self.wacc_mode == 'snapshot':
            snapshot = self.snapshot_lookup.get(ticker, {})
            return float(snapshot.get('WACC', self.default_wacc) or self.default_wacc)
        return float(self.default_wacc)

    def _evaluate_portfolio_horizon(
        self,
        portfolio: pd.DataFrame,
        rebalance_date: pd.Timestamp,
        horizon_months: int,
    ) -> Tuple[pd.DataFrame, float]:
        rows = []
        benchmark_return = self._benchmark_return(rebalance_date, horizon_months)
        if benchmark_return is None:
            return pd.DataFrame(), 0.0
        end_date = rebalance_date + pd.DateOffset(months=horizon_months)
        for _, row in portfolio.iterrows():
            price_info = self._price_info_on_or_before(row['Ticker'], end_date)
            if price_info is None or row['Price'] <= 0:
                continue
            end_price, end_price_date = price_info
            forward_return = (end_price / row['Price']) - 1
            enriched = row.to_dict()
            enriched.update({
                'End_Date': end_date.date().isoformat(),
                'End_Price_Date': end_price_date.date().isoformat(),
                'End_Price': float(end_price),
                'Forward_Return': float(forward_return),
                'Benchmark_Return': float(benchmark_return),
                'Active_Return': float(forward_return - benchmark_return),
            })
            rows.append(enriched)
        return pd.DataFrame(rows), float(benchmark_return)

    @staticmethod
    def _build_summary(holdings_df: pd.DataFrame) -> pd.DataFrame:
        if holdings_df.empty:
            return pd.DataFrame(columns=['Horizon_Months', 'Portfolio_Return', 'Benchmark_Return', 'Active_Return', 'Hit_Rate', 'Observations'])
        summary = holdings_df.groupby('Horizon_Months').agg(
            Portfolio_Return=('Portfolio_Return', 'mean'),
            Benchmark_Return=('Benchmark_Return', 'mean'),
            Active_Return=('Active_Return', 'mean'),
            Hit_Rate=('Hit', 'mean'),
            Observations=('Rebalance_Date', 'count'),
            Avg_Turnover=('Turnover', 'mean'),
            Avg_Universe_Count=('Universe_Count', 'mean'),
            Avg_Excluded_Count=('Excluded_Count', 'mean'),
        ).reset_index()
        summary['Hit_Rate'] = summary['Hit_Rate'] * 100
        return summary

    @staticmethod
    def _build_manifest(
        *,
        signals_df: pd.DataFrame,
        holdings_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        output_path: Path,
        horizons: Sequence[int],
        top_n: int,
        rebalance_frequency: str,
        wacc_mode: str,
    ) -> Dict[str, object]:
        return {
            'output_dir': str(output_path),
            'horizons_months': list(horizons),
            'top_n': top_n,
            'rebalance_frequency': rebalance_frequency,
            'signals': int(len(signals_df)),
            'portfolio_rows': int(len(holdings_df)),
            'exclusion_rows': int(len(exclusions_df)),
            'summary_rows': int(len(summary_df)),
            'no_lookahead_failures': int((~signals_df['No_Lookahead_Pass']).sum()) if 'No_Lookahead_Pass' in signals_df.columns else 0,
            'wacc_mode': wacc_mode,
        }

    @staticmethod
    def _calculate_turnover(previous_tickers: Sequence[str], current_tickers: Sequence[str]) -> float:
        if not previous_tickers:
            return 0.0
        previous = set(previous_tickers)
        current = set(current_tickers)
        if not current:
            return 0.0
        overlap = len(previous & current)
        return 1 - (overlap / max(len(previous), len(current)))

    @staticmethod
    def _build_report(summary_df: pd.DataFrame, manifest: Dict[str, object]) -> str:
        lines = [
            '# Reverse DCF Backtest Report',
            '',
            f"- Rebalance frequency: {manifest['rebalance_frequency']}",
            f"- Horizons (months): {manifest['horizons_months']}",
            f"- Top N portfolio: {manifest['top_n']}",
            f"- Signals generated: {manifest['signals']}",
            '',
            '## Summary',
            '',
        ]
        if summary_df.empty:
            lines.append('No backtest results were generated.')
        else:
            columns = list(summary_df.columns)
            lines.append('| ' + ' | '.join(columns) + ' |')
            lines.append('| ' + ' | '.join(['---'] * len(columns)) + ' |')
            for _, row in summary_df.iterrows():
                lines.append('| ' + ' | '.join(str(row[column]) for column in columns) + ' |')
        return '\n'.join(lines) + '\n'

    @staticmethod
    def _build_audit_report(audit_df: pd.DataFrame, manifest: Dict[str, object]) -> str:
        lines = [
            '# No-Lookahead Audit',
            '',
            f"- WACC mode: {manifest['wacc_mode']}",
            f"- No-lookahead failures: {manifest['no_lookahead_failures']}",
            '',
            'This audit samples the first generated rebalance cross-section. Each sampled row should satisfy:',
            '1. `Availability_Date <= Rebalance_Date`',
            '2. `Price_Date <= Rebalance_Date`',
            '3. backtest WACC mode is fixed (not latest snapshot)',
            '',
        ]
        if audit_df.empty:
            lines.append('No audit rows were generated.')
        else:
            columns = [column for column in ['Ticker', 'Rebalance_Date', 'Availability_Date', 'Price_Date', 'WACC_Mode', 'No_Lookahead_Pass', 'Days_Since_Available'] if column in audit_df.columns]
            lines.append('| ' + ' | '.join(columns) + ' |')
            lines.append('| ' + ' | '.join(['---'] * len(columns)) + ' |')
            for _, row in audit_df[columns].iterrows():
                lines.append('| ' + ' | '.join(str(row[column]) for column in columns) + ' |')
        return '\n'.join(lines) + '\n'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run a reverse DCF backtest on the research bundle.')
    parser.add_argument('--snapshot-path', default='research_data/latest/fundamentals_snapshot.csv')
    parser.add_argument('--observations-path', default='research_data/latest/fundamental_observations.csv')
    parser.add_argument('--price-history-path', default='research_data/latest/price_history.csv')
    parser.add_argument('--benchmark-history-path', default='research_data/latest/benchmark_history.csv')
    parser.add_argument('--output-dir', default='research_data/latest/backtest')
    parser.add_argument('--top-n', type=int, default=10)
    parser.add_argument('--horizons', nargs='*', type=int, default=list(DEFAULT_HORIZONS))
    parser.add_argument('--rebalance-frequency', default='Q')
    parser.add_argument('--start-date', default=None)
    parser.add_argument('--end-date', default=None)
    parser.add_argument('--wacc-mode', default='fixed', choices=['fixed', 'snapshot'])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backtester = ReverseDCFBacktester(
        snapshot_path=args.snapshot_path,
        observations_path=args.observations_path,
        price_history_path=args.price_history_path,
        benchmark_history_path=args.benchmark_history_path,
        wacc_mode=args.wacc_mode,
    )
    result = backtester.run(
        output_dir=args.output_dir,
        horizons=args.horizons,
        top_n=args.top_n,
        rebalance_frequency=args.rebalance_frequency,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
