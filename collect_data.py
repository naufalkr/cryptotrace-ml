#!/usr/bin/env python3
"""
Data Collection Script for CryptoTrace ML

This script connects to the database, fetches all transactions and wallet addresses,
and saves them as JSON files in the data/raw directory.

Usage:
    python collect_data.py                          # Collect all data
    python collect_data.py --limit-tx 1000         # Limit transactions to 1000
    python collect_data.py --limit-wallets 500     # Limit wallets to 500
    python collect_data.py --help                   # Show help
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import collect_and_save_data
from src import config


def main():
    """Main function to run data collection."""
    parser = argparse.ArgumentParser(
        description="Collect transaction and wallet data from database and save as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                 # Collect all data
  %(prog)s --limit-tx 1000                # Limit to 1000 transactions
  %(prog)s --limit-tx 1000 --limit-wallets 500  # Limit both
        """
    )

    parser.add_argument(
        "--limit-tx",
        type=int,
        help="Limit the number of transactions to fetch (default: fetch all)",
        metavar="N"
    )

    parser.add_argument(
        "--limit-wallets",
        type=int,
        help="Limit the number of wallet addresses to fetch (default: fetch all)",
        metavar="N"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for JSON files (default: data/raw)",
        metavar="DIR"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("CryptoTrace ML - Data Collection")
    print("=" * 70)
    print()
    print(f"Output directory: {args.output_dir}")

    if args.limit_tx:
        print(f"Transaction limit: {args.limit_tx}")
    else:
        print("Transaction limit: None (fetching all)")

    if args.limit_wallets:
        print(f"Wallet limit: {args.limit_wallets}")
    else:
        print("Wallet limit: None (fetching all)")

    print()
    print("Note: Make sure you have configured your .env file with database credentials")
    print("      Copy .env.example to .env and fill in your database details")
    print()
    print("-" * 70)
    print()

    # Run data collection
    success = collect_and_save_data(
        output_dir=args.output_dir,
        limit_transactions=args.limit_tx,
        limit_wallets=args.limit_wallets
    )

    print()
    print("=" * 70)

    if success:
        print("✓ Data collection completed successfully!")
        print()
        print("Next steps:")
        print("  1. Run risk scoring: python main.py --mode train")
        print("  2. Run graph analysis: python graph_investigation.py")
        print("=" * 70)
        return 0
    else:
        print("✗ Data collection failed. Please check the error messages above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
