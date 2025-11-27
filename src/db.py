"""
Database connection and data collection module.
Connects to PostgreSQL database and fetches transaction and wallet data.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Any
import json
from decimal import Decimal
from datetime import datetime, date

# Load environment variables from .env file
load_dotenv()


def convert_numeric_types(obj: Any) -> Any:
    """Convert Decimal and other numeric types to appropriate Python types."""
    if isinstance(obj, Decimal):
        # Convert Decimal to float for JSON serialization
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        # Convert datetime to ISO format string
        return obj.isoformat()
    return obj


def process_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Process a database record and convert types appropriately."""
    return {key: convert_numeric_types(value) for key, value in record.items()}


class DatabaseConnection:
    """Handles database connection and queries for cryptocurrency data."""

    def __init__(self):
        """Initialize database connection using environment variables."""
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'cryptotrace'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print(f"[DB] Connected to {self.connection_params['database']} at {self.connection_params['host']}")
            return True
        except psycopg2.Error as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("[DB] Connection closed")

    def fetch_transactions(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch all transactions from the database.

        Args:
            limit: Optional limit on number of transactions to fetch

        Returns:
            List of transaction dictionaries
        """
        if not self.conn:
            raise ConnectionError("Database not connected. Call connect() first.")

        # Adjust this query based on your actual database schema
        query = """
            SELECT
                pkid,
                block_time,
                from_address,
                to_address,
                amount,
                fee,
                raw_data,
                network
            FROM transactions
            ORDER BY block_time DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            self.cursor.execute(query)
            transactions = self.cursor.fetchall()

            # Convert RealDictRow to regular dict and process numeric types
            result = [process_record(dict(row)) for row in transactions]

            print(f"[DB] Fetched {len(result)} transactions")
            return result
        except psycopg2.Error as e:
            print(f"[ERROR] Failed to fetch transactions: {e}")
            return []

    def fetch_wallets(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Fetch all wallet addresses from the database.

        Args:
            limit: Optional limit on number of wallets to fetch

        Returns:
            List of wallet dictionaries
        """
        if not self.conn:
            raise ConnectionError("Database not connected. Call connect() first.")

        # Adjust this query based on your actual database schema
        query = """
            SELECT
                pkid,
                address,
                network,
                total_transactions,
                total_volume_in,
                total_volume_out,
                first_seen_at,
                last_activity_at,
                risk_score,
                risk_level,
                is_monitored,
                is_flagged,
                entity_id,
                notes,
                created_at,
                updated_at,
                deleted_at,
                is_deleted
            FROM wallet_addresses
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            self.cursor.execute(query)
            wallets = self.cursor.fetchall()

            # Convert RealDictRow to regular dict and process numeric types
            result = [process_record(dict(row)) for row in wallets]

            print(f"[DB] Fetched {len(result)} wallets")
            return result
        except psycopg2.Error as e:
            print(f"[ERROR] Failed to fetch wallets: {e}")
            return []

    def update_wallet_risk_scores(self, risk_data: Dict[str, Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Bulk update wallet addresses with risk scores and levels.

        Args:
            risk_data: Dictionary with address as key and dict with risk_score and risk_level
            batch_size: Number of records to update per batch

        Returns:
            Number of successfully updated records
        """
        if not self.conn:
            raise ConnectionError("Database not connected. Call connect() first.")

        if not risk_data:
            print("[WARNING] No risk data provided for update")
            return 0

        update_query = """
            UPDATE wallet_addresses
            SET risk_score = %s,
                risk_level = %s,
                updated_at = NOW()
            WHERE address = %s
        """

        updated_count = 0
        failed_count = 0
        addresses = list(risk_data.keys())
        total = len(addresses)

        print(f"[DB] Updating {total} wallet addresses in batches of {batch_size}...")

        try:
            for i in range(0, total, batch_size):
                batch = addresses[i:i + batch_size]
                batch_data = [
                    (
                        risk_data[addr].get('risk_score', 0.0),
                        risk_data[addr].get('risk_level', 'UNKNOWN'),
                        addr
                    )
                    for addr in batch
                ]

                try:
                    self.cursor.executemany(update_query, batch_data)
                    self.conn.commit()
                    updated_count += len(batch)
                    print(f"[DB] Progress: {updated_count}/{total} updated")
                except psycopg2.Error as e:
                    self.conn.rollback()
                    failed_count += len(batch)
                    print(f"[ERROR] Batch update failed: {e}")

            print(f"[DB] Update complete: {updated_count} successful, {failed_count} failed")
            return updated_count

        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] Bulk update failed: {e}")
            return updated_count


def collect_and_save_data(output_dir: str = "data/raw", limit_transactions: int = None, limit_wallets: int = None):
    """
    Collect data from database and save as JSON files.

    Args:
        output_dir: Directory to save JSON files
        limit_transactions: Optional limit on transactions to fetch
        limit_wallets: Optional limit on wallets to fetch
    """
    db = DatabaseConnection()

    if not db.connect():
        print("[ERROR] Could not establish database connection. Check your .env configuration.")
        return False

    try:
        # Fetch transactions
        print("[INFO] Fetching transactions from database...")
        transactions = db.fetch_transactions(limit=limit_transactions)

        # Save transactions to JSON
        transaction_path = os.path.join(output_dir, "transactions-db.json")
        with open(transaction_path, 'w') as f:
            json.dump(transactions, f, indent=2)
        print(f"[SUCCESS] Saved {len(transactions)} transactions to {transaction_path}")

        # Fetch wallets
        print("[INFO] Fetching wallet addresses from database...")
        wallets = db.fetch_wallets(limit=limit_wallets)

        # Save wallets to JSON
        wallet_path = os.path.join(output_dir, "wallet_addresses-db.json")
        with open(wallet_path, 'w') as f:
            json.dump(wallets, f, indent=2)
        print(f"[SUCCESS] Saved {len(wallets)} wallet addresses to {wallet_path}")

        return True

    except Exception as e:
        print(f"[ERROR] Data collection failed: {e}")
        return False
    finally:
        db.disconnect()


if __name__ == "__main__":
    # Run data collection when executed directly
    import argparse

    parser = argparse.ArgumentParser(description="Collect transaction and wallet data from database")
    parser.add_argument("--limit-tx", type=int, help="Limit number of transactions to fetch")
    parser.add_argument("--limit-wallets", type=int, help="Limit number of wallets to fetch")

    args = parser.parse_args()

    collect_and_save_data(
        limit_transactions=args.limit_tx,
        limit_wallets=args.limit_wallets
    )
