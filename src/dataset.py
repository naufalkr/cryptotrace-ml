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
    
    df['BlockTime'] = pd.to_datetime(df['BlockTime'], utc=True)
    
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
    
    if 'address' in df.columns:
        df.set_index('address', inplace=True)
    
    print(f"   - Loaded {len(df)} wallets")
    return df


def inject_synthetic_bad_actors(df_tx: pd.DataFrame) -> pd.DataFrame:
    if not config.INJECT_SYNTHETIC_DATA:
        print("[DATA] Synthetic injection disabled")
        return df_tx
    
    print("\n[DATA] Injecting synthetic bad actors...")
    
    if not df_tx.empty:
        start_time = df_tx['BlockTime'].min()
    else:
        start_time = pd.Timestamp.now(tz='UTC')
    
    print(f"   - Base time: {start_time}")
    
    fake_txs = []
    
    print(f"   - Smurfing: {config.SMURFING_TX_COUNT} transactions")
    for i in range(config.SMURFING_TX_COUNT):
        fake_txs.append({
            "PKID": 900000 + i,
            "BlockTime": start_time + pd.Timedelta(seconds=i * config.SMURFING_INTERVAL_SECONDS),
            "FromAddress": config.ACTOR_SMURF,
            "ToAddress": f"0xRECEIVER_SMURF_{i}",
            "Amount": config.SMURFING_AMOUNT,
            "Fee": 0.002,
            "RawData": {"input": "0x"},
            "Network": "ethereum-mainnet"
        })
    
    print(f"   - Layering: In {config.LAYERING_AMOUNT_IN} ETH, Out {config.LAYERING_AMOUNT_OUT} ETH")
    fake_txs.append({
        "PKID": 910000,
        "BlockTime": start_time + pd.Timedelta(minutes=5),
        "FromAddress": "0xSOURCE_FUNDS",
        "ToAddress": config.ACTOR_LAYER,
        "Amount": config.LAYERING_AMOUNT_IN,
        "Fee": 0.002,
        "RawData": {"input": "0x"},
        "Network": "ethereum-mainnet"
    })
    fake_txs.append({
        "PKID": 910001,
        "BlockTime": start_time + pd.Timedelta(minutes=5, seconds=config.LAYERING_TIME_DIFF_SECONDS),
        "FromAddress": config.ACTOR_LAYER,
        "ToAddress": "0xFINAL_DEST",
        "Amount": config.LAYERING_AMOUNT_OUT,
        "Fee": 0.002,
        "RawData": {"input": "0x"},
        "Network": "ethereum-mainnet"
    })
    
    print(f"   - Spam Bot: {config.SPAM_TX_COUNT} transactions")
    for i in range(config.SPAM_TX_COUNT):
        fake_txs.append({
            "PKID": 920000 + i,
            "BlockTime": start_time + pd.Timedelta(seconds=i * config.SPAM_INTERVAL_SECONDS),
            "FromAddress": config.ACTOR_SPAM,
            "ToAddress": "0xTARGET_CONTRACT",
            "Amount": config.SPAM_AMOUNT,
            "Fee": 0.002,
            "RawData": {"input": "0x"},
            "Network": "ethereum-mainnet"
        })
    
    df_fake = pd.DataFrame(fake_txs)
    df_combined = pd.concat([df_tx, df_fake], ignore_index=True)
    df_combined['BlockTime'] = pd.to_datetime(df_combined['BlockTime'], utc=True)
    
    print(f"   ✓ Injected {len(fake_txs)} synthetic transactions")
    print(f"   - Total transactions: {len(df_combined)}")
    
    return df_combined


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("="*70)
    print("CRYPTOTRACE DATA LOADING")
    print("="*70)
    
    df_tx = load_transaction_data()
    df_wallet = load_wallet_data()
    
    df_tx = inject_synthetic_bad_actors(df_tx)
    
    return df_tx, df_wallet
