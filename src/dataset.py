import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import warnings

from . import config

warnings.filterwarnings('ignore')


def load_transaction_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    if file_path is None:
        if config.TRANSACTION_JSON_PATH.exists():
            file_path = config.TRANSACTION_JSON_PATH
        elif config.TRANSACTION_CSV_PATH.exists():
            file_path = config.TRANSACTION_CSV_PATH
        else:
            raise FileNotFoundError("No transaction data found in raw data directory")

    print(f"[DATA] Loading transactions from: {file_path}")

    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(file_path)

    # Normalize field names to snake_case (handle both old and new format)
    df.columns = df.columns.str.lower()

    # Map to standard columns
    column_mapping = {
        'blocknumber': 'block_number',
        'blocktime': 'block_time',
        'fromaddress': 'from_address',
        'toaddress': 'to_address',
        'issuspicious': 'is_suspicious',
        'riskscore': 'risk_score',
        'risklevel': 'risk_level'
    }
    df.rename(columns=column_mapping, inplace=True)

    # Ensure required columns exist
    for col in ['from_address', 'to_address', 'block_time']:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Convert datetime
    df['block_time'] = pd.to_datetime(df['block_time'], utc=True)

    # Convert numeric columns
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    df['fee'] = pd.to_numeric(df['fee'], errors='coerce').fillna(0)

    print(f"   - Loaded {len(df)} transactions")
    return df


def load_wallet_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    if file_path is None:
        if config.WALLET_JSON_PATH.exists():
            file_path = config.WALLET_JSON_PATH
        elif config.WALLET_CSV_PATH.exists():
            file_path = config.WALLET_CSV_PATH
        else:
            raise FileNotFoundError("No wallet data found in raw data directory")

    print(f"[DATA] Loading wallets from: {file_path}")

    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(file_path)

    # Normalize field names to snake_case
    df.columns = df.columns.str.lower()

    # Ensure address column exists
    if 'address' not in df.columns:
        raise ValueError("Missing required column: address")

    # Set address as index
    df.set_index('address', inplace=True)

    # Convert numeric columns
    df['total_transactions'] = pd.to_numeric(df['total_transactions'], errors='coerce').fillna(0)
    df['total_volume_in'] = pd.to_numeric(df['total_volume_in'], errors='coerce').fillna(0.0)
    df['total_volume_out'] = pd.to_numeric(df['total_volume_out'], errors='coerce').fillna(0.0)

    print(f"   - Loaded {len(df)} wallets")
    return df


def inject_synthetic_bad_actors(df_tx: pd.DataFrame) -> pd.DataFrame:
    if not config.INJECT_SYNTHETIC_DATA:
        return df_tx

    print("[INFO] Injecting synthetic validation data...")

    if not df_tx.empty:
        start_time = df_tx['block_time'].min()
    else:
        start_time = pd.Timestamp.now(tz='UTC')

    fake_txs = []

    for i in range(config.SMURFING_TX_COUNT):
        fake_txs.append({
            "pkid": 900000 + i,
            "block_time": start_time + pd.Timedelta(seconds=i * config.SMURFING_INTERVAL_SECONDS),
            "from_address": config.ACTOR_SMURF,
            "to_address": f"0xRECEIVER_SMURF_{i}",
            "amount": config.SMURFING_AMOUNT,
            "fee": 0.002,
            "network": "ethereum-mainnet",
            "signature": f"0xSMURF_{i}",
            "is_suspicious": True,
            "status": True,
            "raw_data": "{}"
        })

    fake_txs.append({
        "pkid": 910000,
        "block_time": start_time + pd.Timedelta(minutes=5),
        "from_address": "0xSOURCE_FUNDS",
        "to_address": config.ACTOR_LAYER,
        "amount": config.LAYERING_AMOUNT_IN,
        "fee": 0.002,
        "network": "ethereum-mainnet",
        "signature": "0xLAYER_IN",
        "is_suspicious": True,
        "status": True,
        "raw_data": "{}"
    })
    fake_txs.append({
        "pkid": 910001,
        "block_time": start_time + pd.Timedelta(minutes=5, seconds=config.LAYERING_TIME_DIFF_SECONDS),
        "from_address": config.ACTOR_LAYER,
        "to_address": "0xFINAL_DEST",
        "amount": config.LAYERING_AMOUNT_OUT,
        "fee": 0.002,
        "network": "ethereum-mainnet",
        "signature": "0xLAYER_OUT",
        "is_suspicious": True,
        "status": True,
        "raw_data": "{}"
    })

    for i in range(config.SPAM_TX_COUNT):
        fake_txs.append({
            "pkid": 920000 + i,
            "block_time": start_time + pd.Timedelta(seconds=i * config.SPAM_INTERVAL_SECONDS),
            "from_address": config.ACTOR_SPAM,
            "to_address": "0xTARGET_CONTRACT",
            "amount": config.SPAM_AMOUNT,
            "fee": 0.002,
            "network": "ethereum-mainnet",
            "signature": f"0xSPAM_{i}",
            "is_suspicious": True,
            "status": True,
            "raw_data": "{}"
        })

    df_fake = pd.DataFrame(fake_txs)
    df_combined = pd.concat([df_tx, df_fake], ignore_index=True)
    df_combined['block_time'] = pd.to_datetime(df_combined['block_time'], utc=True)

    print(f"   Injected {len(fake_txs)} synthetic transactions")
    print(f"   - Total transactions: {len(df_combined)}")

    return df_combined


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_tx = load_transaction_data()
    df_wallet = load_wallet_data()

    df_tx = inject_synthetic_bad_actors(df_tx)

    return df_tx, df_wallet
