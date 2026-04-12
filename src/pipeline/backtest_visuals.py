from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class BacktestVisualizer:
    summary_path: str = 'research_data/source_of_truth_100/backtest/summary.csv'
    sector_summary_path: str = 'research_data/source_of_truth_100/backtest/sector_summary.csv'
    sensitivity_path: str = 'research_data/source_of_truth_100/backtest/wacc_sensitivity.csv'

    def __post_init__(self) -> None:
        self.summary = pd.read_csv(self.summary_path)
        self.sector_summary = pd.read_csv(self.sector_summary_path)
        self.sensitivity = pd.read_csv(self.sensitivity_path)

    def generate(self, output_dir: str = 'research_data/source_of_truth_100/backtest/figures') -> Dict[str, str]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        active_return_path = output / 'active_return_by_horizon.png'
        hit_rate_path = output / 'hit_rate_by_horizon.png'
        sector_heatmap_path = output / 'sector_active_return_heatmap.png'
        sensitivity_path = output / 'wacc_sensitivity.png'

        self._plot_active_return(active_return_path)
        self._plot_hit_rate(hit_rate_path)
        self._plot_sector_heatmap(sector_heatmap_path)
        self._plot_wacc_sensitivity(sensitivity_path)

        manifest = {
            'active_return_by_horizon': str(active_return_path),
            'hit_rate_by_horizon': str(hit_rate_path),
            'sector_active_return_heatmap': str(sector_heatmap_path),
            'wacc_sensitivity': str(sensitivity_path),
        }
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest

    def _plot_active_return(self, output_path: Path) -> None:
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = self.summary['Horizon_Months'].astype(str).tolist()
        positions = list(range(len(labels)))
        values = (self.summary['Active_Return'] * 100).tolist()
        ax.bar(positions, values, color='steelblue')
        ax.axhline(0, color='black', linewidth=1)
        ax.set_title('Average Active Return by Horizon')
        ax.set_xlabel('Horizon (Months)')
        ax.set_ylabel('Active Return (%)')
        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
        for x, y in zip(positions, values):
            ax.text(x, y, f'{y:.2f}%', ha='center', va='bottom')
        fig.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)

    def _plot_hit_rate(self, output_path: Path) -> None:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(self.summary['Horizon_Months'], self.summary['Hit_Rate'], marker='o', color='darkgreen')
        ax.set_title('Hit Rate by Horizon')
        ax.set_xlabel('Horizon (Months)')
        ax.set_ylabel('Hit Rate (%)')
        ax.set_xticks(self.summary['Horizon_Months'])
        ax.set_ylim(0, 100)
        for x, y in zip(self.summary['Horizon_Months'], self.summary['Hit_Rate']):
            ax.text(x, y, f'{y:.1f}%', ha='center', va='bottom')
        fig.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)

    def _plot_sector_heatmap(self, output_path: Path) -> None:
        pivot = self.sector_summary.pivot(index='Sector', columns='Horizon_Months', values='Mean_Active_Return').fillna(0) * 100
        fig, ax = plt.subplots(figsize=(10, max(5, len(pivot) * 0.4)))
        image = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
        ax.set_title('Sector Mean Active Return Heatmap (%)')
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([str(column) for column in pivot.columns])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                ax.text(j, i, f'{pivot.iloc[i, j]:.1f}', ha='center', va='center', color='black', fontsize=8)
        fig.colorbar(image, ax=ax, label='Active Return (%)')
        fig.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)

    def _plot_wacc_sensitivity(self, output_path: Path) -> None:
        fig, ax = plt.subplots(figsize=(8, 5))
        for horizon, frame in self.sensitivity.groupby('Horizon_Months'):
            ax.plot(frame['WACC_Assumption'] * 100, frame['Active_Return'] * 100, marker='o', label=f'{int(horizon)}M')
        ax.set_title('WACC Sensitivity of Active Return')
        ax.set_xlabel('Fixed WACC Assumption (%)')
        ax.set_ylabel('Active Return (%)')
        ax.legend(title='Horizon')
        fig.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate thesis-ready backtest figures.')
    parser.add_argument('--summary-path', default='research_data/source_of_truth_100/backtest/summary.csv')
    parser.add_argument('--sector-summary-path', default='research_data/source_of_truth_100/backtest/sector_summary.csv')
    parser.add_argument('--sensitivity-path', default='research_data/source_of_truth_100/backtest/wacc_sensitivity.csv')
    parser.add_argument('--output-dir', default='research_data/source_of_truth_100/backtest/figures')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    visualizer = BacktestVisualizer(
        summary_path=args.summary_path,
        sector_summary_path=args.sector_summary_path,
        sensitivity_path=args.sensitivity_path,
    )
    manifest = visualizer.generate(output_dir=args.output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
