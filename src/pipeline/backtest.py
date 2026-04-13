from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from rdcf.wacc_provider import DamodaranWACCProvider
from reverse_dcf_model import solve_reverse_dcf


DEFAULT_HORIZONS = (3, 6, 12)
DEFAULT_CASE_NAME = 'baseline'
BASELINE_CASE_NAME = 'baseline'
RISK_CONTROL_CASE_NAME = 'risk_control'
DAMODARAN_CASE_NAME = 'damodaran'
DEFAULT_TOP_N_VALUES = (5, 10)
DEFAULT_STOP_LOSS_VALUES = (0.05, 0.10)

# Comprehensive WACC mode configurations (Damodaran NYU Stern framework)
# Each mode isolates a specific WACC dimension for hypothesis testing
COMPREHENSIVE_WACC_MODES = {
    'damodaran_cds': {
        'erp_mode': 'cds',
        'include_size_premium': False,
        'beta_mode': 'fundamental_only',
        'blend_weight': 0.5,
    },
    'damodaran_rating': {
        'erp_mode': 'rating',
        'include_size_premium': False,
        'beta_mode': 'fundamental_only',
        'blend_weight': 0.5,
    },
    'damodaran_size': {
        'erp_mode': 'cds',
        'include_size_premium': True,
        'beta_mode': 'fundamental_only',
        'blend_weight': 0.5,
    },
    'damodaran_beta': {
        'erp_mode': 'cds',
        'include_size_premium': False,
        'beta_mode': 'balanced',
        'blend_weight': 0.5,
    },
    'damodaran_full': {
        'erp_mode': 'rating',
        'include_size_premium': True,
        'beta_mode': 'balanced',
        'blend_weight': 0.5,
    },
    'damodaran_full_cds': {
        'erp_mode': 'cds',
        'include_size_premium': True,
        'beta_mode': 'balanced',
        'blend_weight': 0.5,
    },
    'damodaran_roic': {
        'erp_mode': 'cds',
        'include_size_premium': True,
        'beta_mode': 'balanced',
        'blend_weight': 0.5,
        'roic_screen': True,
    },
}


@dataclass
class ReverseDCFBacktester:
    snapshot_path: str = 'research_data/source_of_truth_100/fundamentals_snapshot.csv'
    observations_path: str = 'research_data/source_of_truth_100/fundamental_observations.csv'
    price_history_path: str = 'research_data/source_of_truth_100/price_history.csv'
    benchmark_history_path: str = 'research_data/source_of_truth_100/benchmark_history.csv'
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

        self.wacc_provider = DamodaranWACCProvider()
        self.ticker_to_industry = self.snapshot.set_index('Ticker')['Industry'].to_dict()

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
        self.max_price_date = pd.Timestamp(self.prices['Date'].max()) if not self.prices.empty else None
        self.max_benchmark_date = pd.Timestamp(self.benchmark['Date'].max()) if not self.benchmark.empty else None

        # Fallback mappings for missing historical metadata (shares, net debt)
        self.earliest_shares: Dict[str, float] = {}
        self.earliest_net_debt: Dict[str, float] = {}
        for ticker, frame in self.observation_lookup.items():
            # Earliest non-zero shares from observations
            valid_shares = frame.loc[frame['Shares_Issued'] > 0, 'Shares_Issued']
            if not valid_shares.empty:
                self.earliest_shares[ticker] = float(valid_shares.iloc[0])
            else:
                # Last resort: snapshot data
                snap = self.snapshot_lookup.get(ticker, {})
                s = snap.get('Shares_Issued') or snap.get('Diluted_Average_Shares')
                if s and s > 0:
                    self.earliest_shares[ticker] = float(s)

            # Earliest non-zero net debt from observations
            valid_debt = frame.loc[frame['Net_Debt'] != 0, 'Net_Debt']
            if not valid_debt.empty:
                self.earliest_net_debt[ticker] = float(valid_debt.iloc[0])
            else:
                # Last resort: snapshot data
                snap = self.snapshot_lookup.get(ticker, {})
                d = snap.get('Net_Debt') or 0
                self.earliest_net_debt[ticker] = float(d)

    def run(
        self,
        output_dir: str = 'research_data/source_of_truth_100/backtest',
        horizons: Sequence[int] = DEFAULT_HORIZONS,
        top_n: int = 10,
        rebalance_frequency: str = 'Q',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        case_name: str = DEFAULT_CASE_NAME,
        stop_loss_pct: Optional[float] = None,
        max_losing_buy_rounds: int = 2,
    ) -> Dict[str, object]:
        effective_case_name, effective_stop_loss_pct = self._normalize_case(case_name, stop_loss_pct)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        rebalance_dates = self._build_rebalance_dates(rebalance_frequency, start_date, end_date)
        signal_rows: List[Dict[str, object]] = []
        holding_rows: List[Dict[str, object]] = []
        exclusion_rows: List[Dict[str, object]] = []
        audit_rows: List[Dict[str, object]] = []
        trade_rows: List[Dict[str, object]] = []
        buy_ban_rows: List[Dict[str, object]] = []
        previous_portfolio: List[str] = []
        losing_buy_rounds: Dict[str, int] = {}
        banned_tickers: set[str] = set()

        for index, rebalance_date in enumerate(rebalance_dates):
            next_rebalance_date = self._next_rebalance_date(rebalance_dates, index, rebalance_date)
            cross_section, exclusions = self._build_cross_section(
                rebalance_date,
                banned_tickers=banned_tickers,
                losing_buy_rounds=losing_buy_rounds,
            )
            if cross_section.empty:
                if not exclusions.empty:
                    exclusions = exclusions.copy()
                    exclusions['Rebalance_Date'] = rebalance_date.date().isoformat()
                    exclusions['Universe_Count'] = len(self.universe_tickers)
                    exclusions['Case_Name'] = effective_case_name
                    exclusions['Top_N_Requested'] = top_n
                    exclusions['Stop_Loss_Pct'] = effective_stop_loss_pct or 0.0
                    exclusion_rows.extend(exclusions.to_dict('records'))
                continue

            universe_count = len(self.universe_tickers)
            excluded_count = len(exclusions)
            ranked = cross_section.sort_values('Signal_Score', ascending=False).reset_index(drop=True)
            ranked['Rebalance_Date'] = rebalance_date.date().isoformat()
            ranked['Universe_Count'] = universe_count
            ranked['Eligible_Count'] = len(ranked)
            ranked['Excluded_Count'] = excluded_count
            ranked['Case_Name'] = effective_case_name
            ranked['Top_N_Requested'] = top_n
            ranked['Stop_Loss_Pct'] = effective_stop_loss_pct or 0.0
            signal_rows.extend(ranked.to_dict('records'))

            if not exclusions.empty:
                exclusions = exclusions.copy()
                exclusions['Rebalance_Date'] = rebalance_date.date().isoformat()
                exclusions['Universe_Count'] = universe_count
                exclusions['Eligible_Count'] = len(ranked)
                exclusions['Case_Name'] = effective_case_name
                exclusions['Top_N_Requested'] = top_n
                exclusions['Stop_Loss_Pct'] = effective_stop_loss_pct or 0.0
                exclusion_rows.extend(exclusions.to_dict('records'))

            if not audit_rows:
                audit_rows = ranked.head(min(10, len(ranked))).to_dict('records')

            portfolio = ranked.head(min(top_n, len(ranked))).copy()
            turnover = self._calculate_turnover(previous_portfolio, portfolio['Ticker'].tolist())
            previous_portfolio = portfolio['Ticker'].tolist()

            round_results = self._evaluate_portfolio_round(
                portfolio=portfolio,
                rebalance_date=rebalance_date,
                next_rebalance_date=next_rebalance_date,
                stop_loss_pct=effective_stop_loss_pct,
                case_name=effective_case_name,
            )
            for round_result in round_results:
                ticker = str(round_result['Ticker'])
                prior_losses = losing_buy_rounds.get(ticker, 0)
                is_losing_round = float(round_result['Realized_Return']) < 0
                updated_losses = prior_losses + int(is_losing_round)
                losing_buy_rounds[ticker] = updated_losses
                ban_triggered = updated_losses > max_losing_buy_rounds
                if ban_triggered:
                    banned_tickers.add(ticker)
                round_result['Prior_Losing_Buy_Rounds'] = prior_losses
                round_result['Losing_Buy_Rounds'] = updated_losses
                round_result['Buy_Ban_Triggered'] = ban_triggered
                round_result['Max_Losing_Buy_Rounds'] = max_losing_buy_rounds
                trade_rows.append(round_result)
                if ban_triggered and prior_losses <= max_losing_buy_rounds:
                    buy_ban_rows.append({
                        'Ticker': ticker,
                        'Ban_Rebalance_Date': rebalance_date.date().isoformat(),
                        'Triggered_By_Exit_Date': round_result['Exit_Date'],
                        'Triggered_By_Return': float(round_result['Realized_Return']),
                        'Losing_Buy_Rounds': updated_losses,
                        'Max_Losing_Buy_Rounds': max_losing_buy_rounds,
                        'Case_Name': effective_case_name,
                        'Top_N': top_n,
                        'Stop_Loss_Pct': effective_stop_loss_pct or 0.0,
                    })

            for horizon in horizons:
                portfolio_holding, benchmark_return = self._evaluate_portfolio_horizon(
                    portfolio=portfolio,
                    rebalance_date=rebalance_date,
                    horizon_months=horizon,
                    stop_loss_pct=effective_stop_loss_pct,
                    case_name=effective_case_name,
                )
                if portfolio_holding.empty:
                    continue
                portfolio_return = portfolio_holding['Forward_Return'].mean()
                holding_rows.append({
                    'Rebalance_Date': rebalance_date.date().isoformat(),
                    'Horizon_Months': horizon,
                    'Case_Name': effective_case_name,
                    'Top_N': len(portfolio_holding),
                    'Top_N_Requested': top_n,
                    'Stop_Loss_Pct': effective_stop_loss_pct or 0.0,
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
                portfolio_holding['Case_Name'] = effective_case_name
                portfolio_holding['Top_N_Requested'] = top_n
                portfolio_holding['Stop_Loss_Pct'] = effective_stop_loss_pct or 0.0
                portfolio_holding.to_csv(
                    output_path / f"portfolio_{rebalance_date.date().isoformat()}_{horizon}m.csv",
                    index=False,
                    encoding='utf-8-sig',
                )

        signals_df = pd.DataFrame(signal_rows)
        holdings_df = pd.DataFrame(holding_rows)
        exclusions_df = pd.DataFrame(exclusion_rows)
        audit_df = pd.DataFrame(audit_rows)
        trade_df = pd.DataFrame(trade_rows)
        buy_ban_df = pd.DataFrame(buy_ban_rows)
        summary_df = self._build_summary(holdings_df)
        summary_df = self._attach_run_metadata(summary_df, effective_case_name, top_n, effective_stop_loss_pct)
        manifest = self._build_manifest(
            signals_df=signals_df,
            holdings_df=holdings_df,
            exclusions_df=exclusions_df,
            summary_df=summary_df,
            trade_df=trade_df,
            buy_ban_df=buy_ban_df,
            output_path=output_path,
            horizons=horizons,
            top_n=top_n,
            rebalance_frequency=rebalance_frequency,
            wacc_mode=self.wacc_mode,
            case_name=effective_case_name,
            stop_loss_pct=effective_stop_loss_pct,
            max_losing_buy_rounds=max_losing_buy_rounds,
        )

        paths = {
            'signals': output_path / 'signals.csv',
            'exclusions': output_path / 'exclusions.csv',
            'portfolio_returns': output_path / 'portfolio_returns.csv',
            'summary': output_path / 'summary.csv',
            'audit_sample': output_path / 'audit_sample.csv',
            'trade_log': output_path / 'trade_log.csv',
            'buy_ban_ledger': output_path / 'buy_ban_ledger.csv',
            'audit_report': output_path / 'no_lookahead_audit.md',
            'report': output_path / 'report.md',
            'manifest': output_path / 'manifest.json',
        }
        signals_df.to_csv(paths['signals'], index=False, encoding='utf-8-sig')
        exclusions_df.to_csv(paths['exclusions'], index=False, encoding='utf-8-sig')
        holdings_df.to_csv(paths['portfolio_returns'], index=False, encoding='utf-8-sig')
        summary_df.to_csv(paths['summary'], index=False, encoding='utf-8-sig')
        audit_df.to_csv(paths['audit_sample'], index=False, encoding='utf-8-sig')
        trade_df.to_csv(paths['trade_log'], index=False, encoding='utf-8-sig')
        buy_ban_df.to_csv(paths['buy_ban_ledger'], index=False, encoding='utf-8-sig')
        paths['audit_report'].write_text(self._build_audit_report(audit_df, manifest), encoding='utf-8')
        paths['report'].write_text(self._build_report(summary_df, manifest), encoding='utf-8')
        paths['manifest'].write_text(json.dumps(manifest, indent=2), encoding='utf-8')

        return {
            'signals': len(signals_df),
            'portfolio_rows': len(holdings_df),
            'summary_rows': len(summary_df),
            'trade_rows': len(trade_df),
            'buy_ban_rows': len(buy_ban_df),
            'paths': {key: str(value) for key, value in paths.items()},
        }

    def run_case_matrix(
        self,
        output_root: str = 'research_data/source_of_truth_100/backtest_cases',
        horizons: Sequence[int] = DEFAULT_HORIZONS,
        top_n_values: Sequence[int] = DEFAULT_TOP_N_VALUES,
        rebalance_frequency: str = 'Q',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        risk_control_stop_losses: Sequence[float] = DEFAULT_STOP_LOSS_VALUES,
        max_losing_buy_rounds: int = 2,
    ) -> Dict[str, object]:
        output_path = Path(output_root)
        output_path.mkdir(parents=True, exist_ok=True)

        summary_frames: List[pd.DataFrame] = []
        case_rows: List[Dict[str, object]] = []
        case_dirs: List[str] = []

        for top_n in top_n_values:
            baseline_dir = output_path / f'baseline_top{top_n}'
            baseline_result = self.run(
                output_dir=str(baseline_dir),
                horizons=horizons,
                top_n=top_n,
                rebalance_frequency=rebalance_frequency,
                start_date=start_date,
                end_date=end_date,
                case_name=BASELINE_CASE_NAME,
                stop_loss_pct=None,
                max_losing_buy_rounds=max_losing_buy_rounds,
            )
            case_dirs.append(str(baseline_dir))
            case_rows.append({
                'Case_Name': BASELINE_CASE_NAME,
                'Top_N': top_n,
                'Stop_Loss_Pct': 0.0,
                'Output_Dir': str(baseline_dir),
                'Signals': baseline_result['signals'],
                'Portfolio_Rows': baseline_result['portfolio_rows'],
                'Trade_Rows': baseline_result['trade_rows'],
                'Buy_Ban_Rows': baseline_result['buy_ban_rows'],
            })
            summary_frames.append(pd.read_csv(baseline_dir / 'summary.csv'))

            for stop_loss_pct in risk_control_stop_losses:
                sl_label = int(round(stop_loss_pct * 100))
                risk_dir = output_path / f'risk_control_top{top_n}_sl{sl_label}'
                risk_result = self.run(
                    output_dir=str(risk_dir),
                    horizons=horizons,
                    top_n=top_n,
                    rebalance_frequency=rebalance_frequency,
                    start_date=start_date,
                    end_date=end_date,
                    case_name=RISK_CONTROL_CASE_NAME,
                    stop_loss_pct=stop_loss_pct,
                    max_losing_buy_rounds=max_losing_buy_rounds,
                )
                case_dirs.append(str(risk_dir))
                case_rows.append({
                    'Case_Name': RISK_CONTROL_CASE_NAME,
                    'Top_N': top_n,
                    'Stop_Loss_Pct': stop_loss_pct,
                    'Output_Dir': str(risk_dir),
                    'Signals': risk_result['signals'],
                    'Portfolio_Rows': risk_result['portfolio_rows'],
                    'Trade_Rows': risk_result['trade_rows'],
                    'Buy_Ban_Rows': risk_result['buy_ban_rows'],
                })
                summary_frames.append(pd.read_csv(risk_dir / 'summary.csv'))

        comparison_summary = pd.concat(summary_frames, ignore_index=True, sort=False) if summary_frames else pd.DataFrame()
        case_manifest_df = pd.DataFrame(case_rows)
        comparison_path = output_path / 'comparison_summary.csv'
        case_manifest_path = output_path / 'case_manifest.csv'
        manifest_path = output_path / 'manifest.json'

        comparison_summary.to_csv(comparison_path, index=False, encoding='utf-8-sig')
        case_manifest_df.to_csv(case_manifest_path, index=False, encoding='utf-8-sig')
        manifest = {
            'case_count': int(len(case_rows)),
            'top_n_values': list(top_n_values),
            'risk_control_stop_losses': list(risk_control_stop_losses),
            'case_output_dirs': case_dirs,
            'paths': {
                'comparison_summary': str(comparison_path),
                'case_manifest': str(case_manifest_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest

    def _normalize_case(self, case_name: str, stop_loss_pct: Optional[float]) -> Tuple[str, Optional[float]]:
        normalized = (case_name or DEFAULT_CASE_NAME).strip().lower()
        valid_cases = {BASELINE_CASE_NAME, RISK_CONTROL_CASE_NAME, DAMODARAN_CASE_NAME} | set(COMPREHENSIVE_WACC_MODES.keys())
        if normalized not in valid_cases:
            raise ValueError(f'Unsupported case_name: {case_name}')
        if normalized in {BASELINE_CASE_NAME, DAMODARAN_CASE_NAME} | set(COMPREHENSIVE_WACC_MODES.keys()):
            return normalized, None
        if stop_loss_pct is None:
            raise ValueError('risk_control case requires --stop-loss-pct')
        if stop_loss_pct <= 0 or stop_loss_pct >= 1:
            raise ValueError('stop_loss_pct must be between 0 and 1')
        return normalized, float(stop_loss_pct)

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

    def _next_rebalance_date(
        self,
        rebalance_dates: Sequence[pd.Timestamp],
        index: int,
        rebalance_date: pd.Timestamp,
    ) -> pd.Timestamp:
        if index + 1 < len(rebalance_dates):
            return pd.Timestamp(rebalance_dates[index + 1])
        return self.max_price_date or rebalance_date

    def _build_cross_section(
        self,
        rebalance_date: pd.Timestamp,
        banned_tickers: Optional[set[str]] = None,
        losing_buy_rounds: Optional[Dict[str, int]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        rows = []
        exclusions = []
        banned_tickers = banned_tickers or set()
        losing_buy_rounds = losing_buy_rounds or {}
        for ticker in self.universe_tickers:
            if ticker in banned_tickers:
                exclusions.append({
                    'Ticker': ticker,
                    'Exclusion_Reason': 'buy_ban_active',
                    'Losing_Buy_Rounds': losing_buy_rounds.get(ticker, 0),
                })
                continue
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
                # ROIC Quality Screen: boost signal for stocks where ROIC > WACC
                # (Damodaran EVA: ROIC > WACC = value creation, Investment Valuation Ch.31)
                # ROIC = NOPAT / Invested Capital = EBIT*(1-t) / (Book Equity + Total Debt - Cash)
                if self.wacc_mode in COMPREHENSIVE_WACC_MODES:
                    mode_config = COMPREHENSIVE_WACC_MODES.get(self.wacc_mode, {})
                    if mode_config.get('roic_screen'):
                        ebit = float(observation.get('EBIT', 0) or 0)
                        total_debt = float(observation.get('Total_Debt', 0) or 0)
                        total_cash = float(observation.get('Total_Cash', 0) or 0)
                        # Estimate book equity from snapshot D/E ratio
                        # (Damodaran ROIC uses book values, not market cap)
                        snap = self.snapshot_lookup.get(ticker, {})
                        de_ratio = float(snap.get('Debt_to_Equity', 0) or 0)
                        if de_ratio > 0:
                            book_equity = total_debt / de_ratio
                        else:
                            shares_obs = observation.get('Diluted_Average_Shares') or observation.get('Shares_Issued') or 0
                            book_equity = float(price * shares_obs)
                        roic = self.wacc_provider.calculate_roic(ebit, total_debt, book_equity, total_cash)
                        wacc_val = row.get('WACC', self.default_wacc)
                        if isinstance(wacc_val, (int, float)):
                            wacc_val = float(wacc_val)
                        else:
                            wacc_val = self.default_wacc
                        # Signal boost: ROIC > WACC stocks get ranked higher
                        # The boost is proportional to the ROIC-WACC spread (EVA spread)
                        if roic > wacc_val and wacc_val > 0:
                            eva_spread = roic - wacc_val
                            row['Signal_Score'] = float(row.get('Signal_Score', 0)) + eva_spread
                        row['ROIC'] = roic
                        row['ROIC_WACC_Spread'] = roic - wacc_val
                row['Losing_Buy_Rounds'] = losing_buy_rounds.get(ticker, 0)
                row['Buy_Ban_Active'] = False
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
        price = self._row_price(row)
        return price, pd.Timestamp(row['Date'])

    def _benchmark_return(self, start_date: pd.Timestamp, horizon_months: int) -> Optional[float]:
        end_date = start_date + pd.DateOffset(months=horizon_months)
        return self._benchmark_return_between(start_date, end_date)

    def _benchmark_return_between(self, start_date: pd.Timestamp, end_date: pd.Timestamp) -> Optional[float]:
        benchmark_start = self._series_price_on_or_before(self.benchmark, start_date)
        benchmark_end = self._series_price_on_or_before(self.benchmark, end_date)
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

    @staticmethod
    def _row_price(row: pd.Series) -> float:
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
            # Fallback to earliest known valid shares if observation is missing it
            shares = self.earliest_shares.get(ticker)
            if not shares:
                return None, 'invalid_shares'

        fcf = observation.get('FCF', 0)
        if pd.isna(fcf) or fcf <= 0:
            return None, 'invalid_fcf'

        # Unit normalization: StockAnalysis scraping uses millions, whereas yfinance uses units.
        # Heuristic: If FCF is < 1M for a SET100 stock (which always has > 1M shares), it is likely in millions.
        if fcf < 1000000 and shares > 1000000:
            fcf *= 1000000

        wacc = self._resolve_wacc(ticker, rebalance_date, observation, price)
        net_debt = observation.get('Net_Debt', 0)
        if pd.isna(net_debt) or net_debt == 0:
            # Fallback to earliest known valid net debt if observation is missing it
            net_debt = self.earliest_net_debt.get(ticker, 0)

        # Ensure net_debt is also scaled if it appears to be in millions
        if 0 < abs(net_debt) < 1000000 and shares > 1000000:
            net_debt *= 1000000

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
            'ERP_Lag_Year': int(rebalance_date.year) - 1 if self.wacc_mode in COMPREHENSIVE_WACC_MODES else 0,
            'ERP_Source': 'dynamic' if self.wacc_mode in COMPREHENSIVE_WACC_MODES else ('damodaran' if self.wacc_mode == 'damodaran' else 'static'),
            'Beta_Mode': COMPREHENSIVE_WACC_MODES.get(self.wacc_mode, {}).get('beta_mode', 'fundamental_only'),
        }, None

    def _resolve_wacc(
        self,
        ticker: str,
        date: Optional[pd.Timestamp] = None,
        observation: Optional[pd.Series] = None,
        price: Optional[float] = None
    ) -> float:
        if self.wacc_mode == 'damodaran' and observation is not None and price is not None:
            industry = self.ticker_to_industry.get(ticker, 'DEFAULT')
            shares = observation.get('Diluted_Average_Shares') or observation.get('Shares_Issued') or 0
            equity_value = float(price * shares)
            total_debt = float(observation.get('Total_Debt', 0))
            ebit = float(observation.get('EBIT', 0))
            interest = float(observation.get('Interest_Expense', 0))

            res = self.wacc_provider.calculate_wacc(
                industry=industry,
                equity_value=equity_value,
                total_debt=total_debt,
                ebit=ebit,
                interest_expense=interest,
                date=date
            )
            return float(res['wacc'])

        # Comprehensive WACC modes (Damodaran NYU Stern framework)
        if self.wacc_mode in COMPREHENSIVE_WACC_MODES and observation is not None and price is not None:
            config = COMPREHENSIVE_WACC_MODES[self.wacc_mode].copy()
            config['ticker'] = ticker
            config['price_lookup'] = self.price_lookup  # Passed from backtest engine
            config['benchmark_df'] = self.benchmark      # SET Index for regression beta

            industry = self.ticker_to_industry.get(ticker, 'DEFAULT')
            shares = observation.get('Diluted_Average_Shares') or observation.get('Shares_Issued') or 0
            equity_value = float(price * shares)
            total_debt = float(observation.get('Total_Debt', 0))
            ebit = float(observation.get('EBIT', 0))
            interest = float(observation.get('Interest_Expense', 0))

            res = self.wacc_provider.calculate_wacc_comprehensive(
                industry=industry,
                equity_value=equity_value,
                total_debt=total_debt,
                ebit=ebit,
                interest_expense=interest,
                date=date,
                config=config,
            )
            return float(res['wacc'])

        if self.wacc_mode == 'snapshot':
            snapshot = self.snapshot_lookup.get(ticker, {})
            return float(snapshot.get('WACC', self.default_wacc) or self.default_wacc)
        return float(self.default_wacc)

    def _evaluate_portfolio_round(
        self,
        portfolio: pd.DataFrame,
        rebalance_date: pd.Timestamp,
        next_rebalance_date: pd.Timestamp,
        stop_loss_pct: Optional[float],
        case_name: str,
    ) -> List[Dict[str, object]]:
        round_rows: List[Dict[str, object]] = []
        benchmark_return = self._benchmark_return_between(rebalance_date, next_rebalance_date)
        benchmark_return = 0.0 if benchmark_return is None else float(benchmark_return)
        for _, row in portfolio.iterrows():
            evaluation = self._evaluate_position_window(
                ticker=row['Ticker'],
                entry_price=float(row['Price']),
                entry_date=rebalance_date,
                end_date=next_rebalance_date,
                stop_loss_pct=stop_loss_pct,
                terminal_exit_reason='rebalance',
            )
            if evaluation is None:
                continue
            round_rows.append({
                'Ticker': row['Ticker'],
                'Rebalance_Date': rebalance_date.date().isoformat(),
                'Round_End_Date': next_rebalance_date.date().isoformat(),
                'Case_Name': case_name,
                'Stop_Loss_Pct': stop_loss_pct or 0.0,
                'Entry_Price': float(row['Price']),
                'Target_Exit_Date': evaluation['Target_End_Date'],
                'Exit_Date': evaluation['Exit_Date'],
                'Exit_Price_Date': evaluation['Exit_Price_Date'],
                'Exit_Price': evaluation['Exit_Price'],
                'Exit_Reason': evaluation['Exit_Reason'],
                'Realized_Return': evaluation['Forward_Return'],
                'Benchmark_Return': benchmark_return,
                'Active_Return': float(evaluation['Forward_Return']) - benchmark_return,
                'Stop_Loss_Hit': evaluation['Stop_Loss_Hit'],
                'Stop_Loss_Trigger_Price': evaluation['Stop_Loss_Trigger_Price'],
            })
        return round_rows

    def _evaluate_portfolio_horizon(
        self,
        portfolio: pd.DataFrame,
        rebalance_date: pd.Timestamp,
        horizon_months: int,
        stop_loss_pct: Optional[float] = None,
        case_name: str = DEFAULT_CASE_NAME,
    ) -> Tuple[pd.DataFrame, float]:
        rows = []
        benchmark_return = self._benchmark_return(rebalance_date, horizon_months)
        if benchmark_return is None:
            return pd.DataFrame(), 0.0
        end_date = rebalance_date + pd.DateOffset(months=horizon_months)
        for _, row in portfolio.iterrows():
            evaluation = self._evaluate_position_window(
                ticker=row['Ticker'],
                entry_price=float(row['Price']),
                entry_date=rebalance_date,
                end_date=end_date,
                stop_loss_pct=stop_loss_pct,
                terminal_exit_reason='horizon_end',
            )
            if evaluation is None or row['Price'] <= 0:
                continue
            enriched = row.to_dict()
            enriched.update({
                'Case_Name': case_name,
                'Target_End_Date': evaluation['Target_End_Date'],
                'End_Date': evaluation['Exit_Date'],
                'End_Price_Date': evaluation['Exit_Price_Date'],
                'End_Price': float(evaluation['Exit_Price']),
                'Exit_Reason': evaluation['Exit_Reason'],
                'Stop_Loss_Hit': evaluation['Stop_Loss_Hit'],
                'Stop_Loss_Pct': stop_loss_pct or 0.0,
                'Stop_Loss_Trigger_Price': evaluation['Stop_Loss_Trigger_Price'],
                'Forward_Return': float(evaluation['Forward_Return']),
                'Benchmark_Return': float(benchmark_return),
                'Active_Return': float(evaluation['Forward_Return'] - benchmark_return),
            })
            rows.append(enriched)
        return pd.DataFrame(rows), float(benchmark_return)

    def _evaluate_position_window(
        self,
        ticker: str,
        entry_price: float,
        entry_date: pd.Timestamp,
        end_date: pd.Timestamp,
        stop_loss_pct: Optional[float],
        terminal_exit_reason: str,
    ) -> Optional[Dict[str, object]]:
        if entry_price <= 0:
            return None
        final_price_info = self._price_info_on_or_before(ticker, end_date)
        if final_price_info is None:
            return None
        exit_price, exit_date = final_price_info
        exit_reason = terminal_exit_reason
        stop_loss_hit = False
        trigger_price = entry_price * (1 - stop_loss_pct) if stop_loss_pct is not None else None

        if stop_loss_pct is not None:
            stop_loss_event = self._first_stop_loss_event(
                ticker=ticker,
                entry_date=entry_date,
                end_date=end_date,
                trigger_price=trigger_price,
            )
            if stop_loss_event is not None:
                exit_price, exit_date = stop_loss_event
                exit_reason = 'stop_loss'
                stop_loss_hit = True

        forward_return = (exit_price / entry_price) - 1
        return {
            'Target_End_Date': pd.Timestamp(end_date).date().isoformat(),
            'Exit_Date': pd.Timestamp(exit_date).date().isoformat(),
            'Exit_Price_Date': pd.Timestamp(exit_date).date().isoformat(),
            'Exit_Price': float(exit_price),
            'Exit_Reason': exit_reason,
            'Forward_Return': float(forward_return),
            'Stop_Loss_Hit': stop_loss_hit,
            'Stop_Loss_Trigger_Price': float(trigger_price) if trigger_price is not None else 0.0,
        }

    def _first_stop_loss_event(
        self,
        ticker: str,
        entry_date: pd.Timestamp,
        end_date: pd.Timestamp,
        trigger_price: Optional[float],
    ) -> Optional[Tuple[float, pd.Timestamp]]:
        if trigger_price is None:
            return None
        frame = self.price_lookup.get(ticker)
        if frame is None or frame.empty:
            return None
        eligible = frame.loc[(frame['Date'] > entry_date) & (frame['Date'] <= end_date)].copy()
        if eligible.empty:
            return None
        eligible['Effective_Close'] = eligible.apply(self._row_price, axis=1)
        triggered = eligible.loc[eligible['Effective_Close'] <= trigger_price]
        if triggered.empty:
            return None
        row = triggered.iloc[0]
        return float(row['Effective_Close']), pd.Timestamp(row['Date'])

    @staticmethod
    def _build_summary(holdings_df: pd.DataFrame) -> pd.DataFrame:
        if holdings_df.empty:
            return pd.DataFrame(columns=[
                'Horizon_Months',
                'Portfolio_Return',
                'Benchmark_Return',
                'Active_Return',
                'Hit_Rate',
                'Observations',
                'Avg_Turnover',
                'Avg_Universe_Count',
                'Avg_Excluded_Count',
            ])
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
    def _attach_run_metadata(
        summary_df: pd.DataFrame,
        case_name: str,
        top_n: int,
        stop_loss_pct: Optional[float],
    ) -> pd.DataFrame:
        if summary_df.empty:
            summary_df = summary_df.copy()
            summary_df['Case_Name'] = pd.Series(dtype='object')
            summary_df['Top_N'] = pd.Series(dtype='int64')
            summary_df['Stop_Loss_Pct'] = pd.Series(dtype='float64')
            return summary_df
        summary_df = summary_df.copy()
        summary_df['Case_Name'] = case_name
        summary_df['Top_N'] = top_n
        summary_df['Stop_Loss_Pct'] = stop_loss_pct or 0.0
        return summary_df

    def _build_manifest(
        self,
        *,
        signals_df: pd.DataFrame,
        holdings_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        trade_df: pd.DataFrame,
        buy_ban_df: pd.DataFrame,
        output_path: Path,
        horizons: Sequence[int],
        top_n: int,
        rebalance_frequency: str,
        wacc_mode: str,
        case_name: str,
        stop_loss_pct: Optional[float],
        max_losing_buy_rounds: int,
    ) -> Dict[str, object]:
        return {
            'output_dir': str(output_path),
            'case_name': case_name,
            'daily_stop_loss_enabled': stop_loss_pct is not None,
            'stop_loss_pct': float(stop_loss_pct) if stop_loss_pct is not None else 0.0,
            'max_losing_buy_rounds': max_losing_buy_rounds,
            'horizons_months': list(horizons),
            'top_n': top_n,
            'rebalance_frequency': rebalance_frequency,
            'signals': int(len(signals_df)),
            'portfolio_rows': int(len(holdings_df)),
            'trade_rows': int(len(trade_df)),
            'buy_ban_rows': int(len(buy_ban_df)),
            'exclusion_rows': int(len(exclusions_df)),
            'summary_rows': int(len(summary_df)),
            'no_lookahead_failures': int((~signals_df['No_Lookahead_Pass']).sum()) if 'No_Lookahead_Pass' in signals_df.columns else 0,
            'wacc_mode': wacc_mode,
            'input_bundle_dir': str(Path(self.observations_path).parent),
            'input_bundle_source': 'scraping_first_hybrid',
            'universe_size': len(self.universe_tickers),
            'methodology': 'Damodaran Stern Reverse DCF',
            'framework_reference': 'https://pages.stern.nyu.edu/~adamodar/New_Home_Page/home.htm',
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
            f"- Case: {manifest['case_name']}",
            f"- Rebalance frequency: {manifest['rebalance_frequency']}",
            f"- Horizons (months): {manifest['horizons_months']}",
            f"- Top N portfolio: {manifest['top_n']}",
            f"- Daily stop-loss enabled: {manifest['daily_stop_loss_enabled']}",
            f"- Stop-loss pct: {manifest['stop_loss_pct']}",
            f"- Buy ban threshold (losing buy rounds): {manifest['max_losing_buy_rounds']}",
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
        
        lines.extend([
            '',
            '---',
            '**Methodology Note**: This backtest employs the Damodaran Stern Reverse DCF framework for growth implication analysis.',
            'For detailed formula mapping and theoretical foundations, see `METHODOLOGY.md` and Damodaran\'s lecture materials on intrinsic valuation.',
            f"Framework Reference: {manifest.get('framework_reference', 'N/A')}"
        ])
        
        return '\n'.join(lines) + '\n'

    @staticmethod
    def _build_audit_report(audit_df: pd.DataFrame, manifest: Dict[str, object]) -> str:
        lines = [
            '# No-Lookahead Audit',
            '',
            f"- Case: {manifest['case_name']}",
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
    parser = argparse.ArgumentParser(
        description='Run a reverse DCF backtest on the research bundle using the Damodaran Stern framework.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--snapshot-path', default='research_data/source_of_truth_100/fundamentals_snapshot.csv', help='Path to fundamentals snapshot CSV')
    parser.add_argument('--observations-path', default='research_data/source_of_truth_100/fundamental_observations.csv', help='Path to fundamental observations CSV')
    parser.add_argument('--price-history-path', default='research_data/source_of_truth_100/price_history.csv', help='Path to price history CSV')
    parser.add_argument('--benchmark-history-path', default='research_data/source_of_truth_100/benchmark_history.csv', help='Path to benchmark history CSV')
    parser.add_argument('--output-dir', default='research_data/source_of_truth_100/backtest', help='Output directory for backtest results')
    parser.add_argument('--top-n', type=int, default=10, help='Number of top stocks to include in portfolio (Damodaran-style selection)')
    parser.add_argument('--top-n-values', nargs='*', type=int, default=list(DEFAULT_TOP_N_VALUES), help='Top-N values for matrix run')
    parser.add_argument('--horizons', nargs='*', type=int, default=list(DEFAULT_HORIZONS), help='Return horizons in months')
    parser.add_argument('--rebalance-frequency', default='Q', help='Rebalance frequency (e.g., Q for quarterly alignment with fundamentals)')
    parser.add_argument('--start-date', default=None, help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=None, help='Backtest end date (YYYY-MM-DD)')
    parser.add_argument('--wacc-mode', default='fixed', choices=['fixed', 'snapshot', 'damodaran', 'damodaran_cds', 'damodaran_rating', 'damodaran_size', 'damodaran_beta', 'damodaran_full', 'damodaran_full_cds'], help='WACC calculation mode')
    parser.add_argument('--case-name', default=DEFAULT_CASE_NAME, choices=[BASELINE_CASE_NAME, RISK_CONTROL_CASE_NAME, DAMODARAN_CASE_NAME, 'damodaran_cds', 'damodaran_rating', 'damodaran_size', 'damodaran_beta', 'damodaran_full', 'damodaran_full_cds'], help='Case name for single run')
    parser.add_argument('--stop-loss-pct', type=float, default=None, help='Stop loss percentage for risk_control case (e.g., 0.1 for 10 percent)')
    parser.add_argument('--stop-loss-values', nargs='*', type=float, default=list(DEFAULT_STOP_LOSS_VALUES), help='Stop loss values for matrix run (risk_control cases)')
    parser.add_argument('--max-losing-buy-rounds', type=int, default=2, help='Maximum number of losing buy rounds before permanent ban (Damodaran-style persistence check)')
    parser.add_argument('--matrix', action='store_true', help='Run a matrix of backtest cases based on the Damodaran quarterly rebalance plan (baseline + risk_control)')
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
    if args.matrix:
        result = backtester.run_case_matrix(
            output_root=args.output_dir,
            horizons=args.horizons,
            top_n_values=args.top_n_values,
            rebalance_frequency=args.rebalance_frequency,
            start_date=args.start_date,
            end_date=args.end_date,
            risk_control_stop_losses=args.stop_loss_values,
            max_losing_buy_rounds=args.max_losing_buy_rounds,
        )
    else:
        result = backtester.run(
            output_dir=args.output_dir,
            horizons=args.horizons,
            top_n=args.top_n,
            rebalance_frequency=args.rebalance_frequency,
            start_date=args.start_date,
            end_date=args.end_date,
            case_name=args.case_name,
            stop_loss_pct=args.stop_loss_pct,
            max_losing_buy_rounds=args.max_losing_buy_rounds,
        )
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
