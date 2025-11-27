#!/usr/bin/env python3
"""
Risk Score Update Script for CryptoTrace ML

This script reads the risk scoring results and updates the wallet_addresses table
in the database with the calculated risk scores and levels.

Usage:
    python update_risk_scores.py                          # Update from default file
    python update_risk_scores.py --input custom.json     # Update from custom file
    python update_risk_scores.py --batch-size 500        # Custom batch size
    python update_risk_scores.py --dry-run               # Preview without updating
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import DatabaseConnection
from src import config


def load_risk_scores(file_path: str) -> dict:
    """
    Load risk scores from JSON file.

    Args:
        file_path: Path to the risk scores JSON file

    Returns:
        Dictionary with address as key and risk data as value
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"[INFO] Loaded {len(data)} risk scores from {file_path}")
        return data
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON format: {e}")
        return {}


def preview_updates(risk_data: dict, limit: int = 10):
    """
    Preview the updates that will be made.

    Args:
        risk_data: Risk score data dictionary
        limit: Number of records to preview
    """
    print("\n" + "=" * 70)
    print("PREVIEW OF UPDATES")
    print("=" * 70)
    print(f"{'Address':<45} {'Risk Score':<12} {'Risk Level':<12}")
    print("-" * 70)

    count = 0
    for address, data in risk_data.items():
        if count >= limit:
            print(f"... and {len(risk_data) - limit} more records")
            break
        risk_score = data.get('risk_score', 0.0)
        risk_level = data.get('risk_level', 'UNKNOWN')
        print(f"{address:<45} {risk_score:<12.2f} {risk_level:<12}")
        count += 1

    print("=" * 70 + "\n")


def update_database(risk_data: dict, batch_size: int = 100, dry_run: bool = False) -> bool:
    """
    Update the database with risk scores.

    Args:
        risk_data: Risk score data dictionary
        batch_size: Number of records to update per batch
        dry_run: If True, only preview without updating

    Returns:
        True if successful, False otherwise
    """
    if not risk_data:
        print("[ERROR] No risk data to update")
        return False

    if dry_run:
        print("[DRY RUN] Previewing updates without modifying database...")
        preview_updates(risk_data, limit=20)
        print(f"[DRY RUN] Would update {len(risk_data)} wallet addresses")
        return True

    db = DatabaseConnection()

    if not db.connect():
        print("[ERROR] Could not establish database connection. Check your .env configuration.")
        return False

    try:
        print(f"[INFO] Starting bulk update of {len(risk_data)} wallet addresses...")
        updated_count = db.update_wallet_risk_scores(risk_data, batch_size=batch_size)

        if updated_count > 0:
            print(f"[SUCCESS] Updated {updated_count} wallet addresses in database")
            return True
        else:
            print("[WARNING] No records were updated")
            return False

    except Exception as e:
        print(f"[ERROR] Update failed: {e}")
        return False
    finally:
        db.disconnect()


def main():
    """Main function to run risk score updates."""
    parser = argparse.ArgumentParser(
        description="Update wallet addresses in database with calculated risk scores",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                      # Update from default file
  %(prog)s --input custom_scores.json          # Update from custom file
  %(prog)s --batch-size 500                    # Use larger batches
  %(prog)s --dry-run                           # Preview without updating
  %(prog)s --input scores.json --batch-size 200 --dry-run
        """
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(config.RISK_SCORED_JSON_PATH),
        help=f"Path to risk scores JSON file (default: {config.RISK_SCORED_JSON_PATH})",
        metavar="FILE"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to update per batch (default: 100)",
        metavar="N"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview updates without modifying the database"
    )

    parser.add_argument(
        "--preview",
        type=int,
        default=10,
        help="Number of records to preview (default: 10)",
        metavar="N"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CryptoTrace ML - Risk Score Database Update")
    print("=" * 70)
    print()
    print(f"Input file: {args.input}")
    print(f"Batch size: {args.batch_size}")
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'LIVE UPDATE'}")
    print()

    if not args.dry_run:
        print("⚠️  WARNING: This will UPDATE the database!")
        print("   Make sure you have a backup before proceeding.")
        print()

    print("-" * 70)
    print()

    # Load risk scores
    risk_data = load_risk_scores(args.input)

    if not risk_data:
        print("[ERROR] No valid risk data loaded. Exiting.")
        return 1

    # Preview some records
    if not args.dry_run:
        preview_updates(risk_data, limit=args.preview)

    # Update database
    success = update_database(
        risk_data=risk_data,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    print()
    print("=" * 70)

    if success:
        if args.dry_run:
            print("✓ Dry run completed successfully!")
            print("  Run without --dry-run to perform the actual update.")
        else:
            print("✓ Database update completed successfully!")
            print()
            print("Risk scores have been updated in the wallet_addresses table.")
        print("=" * 70)
        return 0
    else:
        print("✗ Update failed. Please check the error messages above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
