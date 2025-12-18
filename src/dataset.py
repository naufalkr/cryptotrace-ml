import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import warnings

from . import config

warnings.filterwarnings('ignore')


def load_all_transaction_files() -> List[Path]:
    """Auto-detect all transaction JSON files in raw data directory."""
    raw_dir = config.RAW_DATA_DIR
    tx_files = []
    
    for pattern in ['*transactions*.json', 'transactions-*.json']:
        tx_files.extend(raw_dir.glob(pattern))
    
    tx_files = list(set(tx_files))
    return sorted(tx_files)


def normalize_transaction_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize transaction dataframe to standard format."""
    
    df.columns = df.columns.str.lower()
    
    column_mapping = {
        'blocknumber': 'block_number',
        'blocktime': 'block_time',
        'fromaddress': 'from_address',
        'toaddress': 'to_address',
        'issuspicious': 'is_suspicious',
        'riskscore': 'risk_score',
        'risklevel': 'risk_level',
        'signature': 'signature',
        'tokenaddress': 'token_address',
        'tokenamount': 'token_amount',
        'tokendecimals': 'token_decimals'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    for col in ['from_address', 'to_address', 'block_time']:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    df['block_time'] = pd.to_datetime(df['block_time'], utc=True)
    
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    df['fee'] = pd.to_numeric(df['fee'], errors='coerce').fillna(0)
    
    if 'network' not in df.columns:
        df['network'] = 'unknown'
    
    if 'pkid' not in df.columns and 'PKID' in df.columns:
        df['pkid'] = df['PKID']
    
    return df


def load_transaction_data(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load transaction data from single or multiple files."""
    
    if file_path is None:
        tx_files = load_all_transaction_files()
        
        if not tx_files:
            raise FileNotFoundError("No transaction data found in raw data directory")
        
        print(f"[DATA] Found {len(tx_files)} transaction file(s)")
        
        all_dfs = []
        for tx_file in tx_files:
            print(f"[DATA] Loading: {tx_file.name}")
            
            with open(tx_file, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df = normalize_transaction_dataframe(df)
            
            print(f"   - Loaded {len(df)} transactions from {tx_file.name}")
            all_dfs.append(df)
        
        df_combined = pd.concat(all_dfs, ignore_index=True)
        print(f"[DATA] Total transactions loaded: {len(df_combined)}")
        
        if 'network' in df_combined.columns:
            network_counts = df_combined['network'].value_counts()
            print(f"[DATA] Networks: {dict(network_counts)}")
        
        return df_combined
    
    else:
        print(f"[DATA] Loading transactions from: {file_path}")
        
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            df = pd.read_csv(file_path)
        
        df = normalize_transaction_dataframe(df)
        print(f"   - Loaded {len(df)} transactions")
        return df


def generate_wallet_data_from_transactions(df_tx: pd.DataFrame) -> pd.DataFrame:
    """Generate wallet data from transactions if wallet file doesn't exist."""
    print("[DATA] Generating wallet data from transactions...")
    
    all_addresses = pd.concat([
        df_tx['from_address'],
        df_tx['to_address']
    ]).unique()
    
    wallet_data = []
    for addr in all_addresses:
        sent_txs = df_tx[df_tx['from_address'] == addr]
        received_txs = df_tx[df_tx['to_address'] == addr]
        
        total_tx = len(sent_txs) + len(received_txs)
        volume_out = sent_txs['amount'].sum()
        volume_in = received_txs['amount'].sum()
        
        wallet_data.append({
            'address': addr,
            'total_transactions': total_tx,
            'total_volume_in': volume_in,
            'total_volume_out': volume_out
        })
    
    df_wallet = pd.DataFrame(wallet_data)
    df_wallet.set_index('address', inplace=True)
    
    print(f"   - Generated {len(df_wallet)} wallet profiles")
    return df_wallet


def load_wallet_data(file_path: Optional[Path] = None, df_tx: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Load wallet data from file or generate from transactions."""
    
    if file_path is None:
        if config.WALLET_JSON_PATH.exists():
            file_path = config.WALLET_JSON_PATH
        else:
            print("[DATA] No wallet file found, will generate from transactions")
            if df_tx is None:
                raise ValueError("Cannot generate wallet data without transaction data")
            return generate_wallet_data_from_transactions(df_tx)
    
    print(f"[DATA] Loading wallets from: {file_path}")
    
    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(file_path)
    
    df.columns = df.columns.str.lower()
    
    if 'address' not in df.columns:
        raise ValueError("Missing required column: address")
    
    df.set_index('address', inplace=True)
    
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
    """Load transaction and wallet data with auto-detection and generation."""
    df_tx = load_transaction_data()
    
    df_wallet = load_wallet_data(df_tx=df_tx)
    
    df_tx = inject_synthetic_bad_actors(df_tx)
    
    return df_tx, df_wallet
