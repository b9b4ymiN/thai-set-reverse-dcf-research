from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_FILES = [
    'docs/thesis-methodology.md',
    'docs/thesis-results.md',
    'docs/executive-summary.md',
    'docs/presentation-script.md',
    'docs/defense-outline.md',
    'docs/q-and-a-sheet.md',
    'research_data/source_of_truth_100/backtest/report.md',
    'research_data/source_of_truth_100/backtest/appendix.md',
    'research_data/source_of_truth_100/backtest/summary.csv',
    'research_data/source_of_truth_100/backtest/exclusions.csv',
    'research_data/source_of_truth_100/backtest/no_lookahead_audit.md',
    'research_data/source_of_truth_100/backtest/sector_summary.csv',
    'research_data/source_of_truth_100/backtest/wacc_sensitivity.csv',
    'research_data/source_of_truth_100/backtest/figures/active_return_by_horizon.png',
    'research_data/source_of_truth_100/backtest/figures/hit_rate_by_horizon.png',
    'research_data/source_of_truth_100/backtest/figures/sector_active_return_heatmap.png',
    'research_data/source_of_truth_100/backtest/figures/wacc_sensitivity.png',
]


@dataclass
class ThesisBundleBuilder:
    files: List[str] = None

    def __post_init__(self) -> None:
        self.files = list(DEFAULT_FILES if self.files is None else self.files)

    def build(self, output_dir: str = 'research_data/source_of_truth_100/thesis_bundle') -> Dict[str, object]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        copied = []
        missing = []
        for rel_path in self.files:
            src = Path(rel_path)
            if not src.exists():
                missing.append(rel_path)
                continue
            dest = output / src.name
            shutil.copy2(src, dest)
            copied.append({'source': rel_path, 'dest': str(dest)})

        readme_path = output / 'README.md'
        readme_path.write_text(self._build_readme(copied, missing), encoding='utf-8')
        manifest = {
            'output_dir': str(output),
            'copied_count': len(copied),
            'missing_count': len(missing),
            'copied': copied,
            'missing': missing,
            'readme': str(readme_path),
        }
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest

    @staticmethod
    def _build_readme(copied: List[Dict[str, str]], missing: List[str]) -> str:
        lines = [
            '# Thesis Bundle',
            '',
            'This folder collects the latest methodology, results, appendix, and figure artifacts for thesis or presentation use.',
            '',
            '## Included files',
            '',
        ]
        for item in copied:
            lines.append(f"- `{Path(item['dest']).name}` ← `{item['source']}`")
        if missing:
            lines.extend(['', '## Missing files', ''])
            lines.extend(f'- `{item}`' for item in missing)
        lines.append('')
        return '\n'.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Package thesis-ready artifacts into one bundle directory.')
    parser.add_argument('--output-dir', default='research_data/source_of_truth_100/thesis_bundle')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    builder = ThesisBundleBuilder()
    manifest = builder.build(output_dir=args.output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
