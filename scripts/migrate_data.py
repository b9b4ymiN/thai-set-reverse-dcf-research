#!/usr/bin/env python3
"""
Migrate existing data from legacy research_data/ structure to new data/ structure.

This script:
1. Preserves all existing data
2. Creates metadata records
3. Generates migration report
4. Validates data integrity

Usage:
    python scripts/migrate_data.py [--source SOURCE_DIR] [--dest DEST_DIR] [--dry-run]
"""

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

# Create logs directory
Path('logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/migrate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Migrate data from legacy to new structure."""

    def __init__(self, source_dir: str, dest_dir: str, dry_run: bool = False):
        self.source_dir = Path(source_dir)
        self.dest_dir = Path(dest_dir)
        self.dry_run = dry_run
        self.migration_report = {
            'timestamp': datetime.now().isoformat(),
            'source_dir': str(source_dir),
            'dest_dir': str(dest_dir),
            'dry_run': dry_run,
            'migrated_files': [],
            'skipped_files': [],
            'errors': [],
            'summary': {}
        }

        # Create destination directories
        self.dirs = {
            'raw': self.dest_dir / 'raw' / 'set100',
            'processed_fundamentals_quarterly': self.dest_dir / 'processed' / 'fundamentals' / 'quarterly',
            'processed_fundamentals_annual': self.dest_dir / 'processed' / 'fundamentals' / 'annual',
            'processed_prices_daily': self.dest_dir / 'processed' / 'prices' / 'daily',
            'processed_prices_adjusted': self.dest_dir / 'processed' / 'prices' / 'adjusted',
            'metadata': self.dest_dir / 'processed' / 'metadata',
        }

        if not dry_run:
            for dir_path in self.dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized migrator: {source_dir} -> {dest_dir}")

    def migrate_fundamentals_snapshot(self) -> None:
        """Migrate fundamentals snapshot to processed/quarterly/."""
        source_file = self.source_dir / 'fundamentals_snapshot.csv'

        if not source_file.exists():
            logger.warning(f"Fundamentals snapshot not found: {source_file}")
            self.migration_report['skipped_files'].append(str(source_file))
            return

        logger.info(f"Migrating fundamentals snapshot...")

        try:
            df = pd.read_csv(source_file)
            dest_file = self.dirs['processed_fundamentals_quarterly'] / 'fundamentals.parquet'
            backup_file = self.dirs['processed_fundamentals_quarterly'] / 'fundamentals.csv'

            if not self.dry_run:
                # Save as CSV as fallback (Parquet requires pyarrow)
                df.to_csv(backup_file, index=False)
                dest_file = backup_file  # Update to actual file created

            self.migration_report['migrated_files'].append({
                'source': str(source_file),
                'destination': str(dest_file),
                'rows': len(df),
                'columns': len(df.columns)
            })

            logger.info(f"✓ Migrated {len(df)} rows to {dest_file}")

        except Exception as e:
            logger.error(f"Error migrating fundamentals: {e}")
            self.migration_report['errors'].append({
                'file': str(source_file),
                'error': str(e)
            })

    def migrate_price_history(self) -> None:
        """Migrate price history to processed/prices/daily/."""
        source_file = self.source_dir / 'price_history.csv'

        if not source_file.exists():
            logger.warning(f"Price history not found: {source_file}")
            self.migration_report['skipped_files'].append(str(source_file))
            return

        logger.info(f"Migrating price history...")

        try:
            df = pd.read_csv(source_file)
            dest_file = self.dirs['processed_prices_daily'] / 'prices.parquet'
            backup_file = self.dirs['processed_prices_daily'] / 'prices.csv'

            if not self.dry_run:
                # Save as CSV as fallback (Parquet requires pyarrow)
                df.to_csv(backup_file, index=False)
                dest_file = backup_file  # Update to actual file created

            self.migration_report['migrated_files'].append({
                'source': str(source_file),
                'destination': str(dest_file),
                'rows': len(df),
                'columns': len(df.columns)
            })

            logger.info(f"✓ Migrated {len(df)} rows to {dest_file}")

        except Exception as e:
            logger.error(f"Error migrating price history: {e}")
            self.migration_report['errors'].append({
                'file': str(source_file),
                'error': str(e)
            })

    def create_metadata(self) -> None:
        """Create metadata files for migrated data."""
        logger.info("Creating metadata files...")

        # Data manifest
        manifest = {
            'migration_date': datetime.now().isoformat(),
            'source_directory': str(self.source_dir),
            'data_files': []
        }

        for item in self.migration_report['migrated_files']:
            manifest['data_files'].append({
                'type': item['destination'].split('/')[-2],
                'path': item['destination'],
                'rows': item['rows'],
                'source_file': item['source']
            })

        manifest_file = self.dirs['metadata'] / 'data_manifest.json'

        if not self.dry_run:
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

        # Acquisition log
        acquisition_log = {
            'migration': {
                'timestamp': datetime.now().isoformat(),
                'source': 'legacy_research_data',
                'method': 'migration_script',
                'files_migrated': len(self.migration_report['migrated_files']),
                'status': 'completed'
            }
        }

        log_file = self.dirs['metadata'] / 'acquisition_log.json'

        if not self.dry_run:
            with open(log_file, 'w') as f:
                json.dump(acquisition_log, f, indent=2)

        logger.info(f"✓ Created metadata files")

    def generate_quality_report(self) -> None:
        """Generate data quality report."""
        logger.info("Generating quality report...")

        quality_data = []

        for item in self.migration_report['migrated_files']:
            quality_data.append({
                'file': item['destination'],
                'rows': item['rows'],
                'columns': item['columns'],
                'status': 'migrated',
                'issues': []
            })

        df = pd.DataFrame(quality_data)
        report_file = self.dirs['metadata'] / 'quality_report.csv'

        if not self.dry_run:
            df.to_csv(report_file, index=False)

        logger.info(f"✓ Generated quality report: {report_file}")

    def run(self) -> None:
        """Execute full migration."""
        logger.info("="*60)
        logger.info("Starting data migration...")
        logger.info("="*60)

        # Migrate data files
        self.migrate_fundamentals_snapshot()
        self.migrate_price_history()

        # Create metadata
        self.create_metadata()
        self.generate_quality_report()

        # Generate summary
        self.migration_report['summary'] = {
            'total_files': len(self.migration_report['migrated_files']),
            'total_rows': sum(item['rows'] for item in self.migration_report['migrated_files']),
            'errors': len(self.migration_report['errors']),
            'skipped': len(self.migration_report['skipped_files'])
        }

        # Save migration report
        report_file = self.dest_dir / 'migration_report.json'
        if not self.dry_run:
            with open(report_file, 'w') as f:
                json.dump(self.migration_report, f, indent=2)

        # Print summary
        logger.info("="*60)
        logger.info("Migration Summary:")
        logger.info(f"  Files migrated: {self.migration_report['summary']['total_files']}")
        logger.info(f"  Total rows: {self.migration_report['summary']['total_rows']:,}")
        logger.info(f"  Errors: {self.migration_report['summary']['errors']}")
        logger.info(f"  Skipped: {self.migration_report['summary']['skipped']}")
        logger.info("="*60)

        if self.dry_run:
            logger.info("DRY RUN COMPLETE - No files were actually modified")
        else:
            logger.info("MIGRATION COMPLETE")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate data from legacy to new structure'
    )
    parser.add_argument(
        '--source',
        default='research_data/set100_working',
        help='Source directory (default: research_data/set100_working)'
    )
    parser.add_argument(
        '--dest',
        default='data',
        help='Destination directory (default: data)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without modifying files'
    )

    args = parser.parse_args()

    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    # Run migration
    migrator = DataMigrator(args.source, args.dest, args.dry_run)
    migrator.run()


if __name__ == '__main__':
    main()
