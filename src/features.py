import pandas as pd
import numpy as np
from typing import Tuple

from . import config


def engineer_transaction_features(df_tx: pd.DataFrame) -> pd.DataFrame:
    print("\n[FEATURES] Engineering transaction features...")
    
    df_tx['amount'] = df_tx['amount'].fillna(0)
    df_tx['fee'] = df_tx['fee'].fillna(0)
    df_tx['gas_fee_ratio'] = np.where(df_tx['amount'] > 0, df_tx['fee'] / df_tx['amount'], 0)
    
    def is_round(amount):
        if amount > 0 and amount in config.ROUND_AMOUNTS:
            return 1
        return 0
    
    df_tx['is_round'] = df_tx['amount'].apply(is_round)
    
    return df_tx


def get_wallet_features(df_tx: pd.DataFrame, address_col: str) -> pd.DataFrame:
    grp = df_tx.groupby(address_col)
    
    features = grp.agg({
        'pkid': 'count',
        'amount': ['sum', 'mean', 'max'],
        'gas_fee_ratio': 'mean',
        'is_round': 'mean'
    })
    
    features.columns = ['_'.join(col).strip() for col in features.columns.values]
    features.rename(columns={'pkid_count': 'tx_count'}, inplace=True)
    
    def avg_time_diff(x):
        if len(x) < 2:
            return 0
        return x.sort_values().diff().dt.total_seconds().mean()
    
    features['avg_seconds_between_tx'] = grp['block_time'].apply(avg_time_diff)
    
    c_col = 'to_address' if address_col == 'from_address' else 'from_address'
    features['unique_counterparties'] = grp[c_col].nunique()
    
    def tx_velocity(x):
        if len(x) < 2:
            return 0
        duration_min = (x.max() - x.min()).total_seconds() / 60
        return len(x) / (duration_min + 1)
    
    features['tx_per_minute'] = grp['block_time'].apply(tx_velocity)
    
    return features


def aggregate_wallet_profiles(df_tx: pd.DataFrame, df_wallet: pd.DataFrame) -> pd.DataFrame:
    print("\n[FEATURES] Aggregating wallet profiles...")
    
    df_from = get_wallet_features(df_tx, 'from_address')
    df_to = get_wallet_features(df_tx, 'to_address')
    
    df_from.columns = ['snd_' + c for c in df_from.columns]
    df_to.columns = ['rcv_' + c for c in df_to.columns]
    
    final_df = df_wallet.join(df_from, how='outer').join(df_to, how='outer').fillna(0)
    active_wallets = final_df[(final_df['snd_tx_count'] > 0) | (final_df['rcv_tx_count'] > 0)].copy()
    
    return active_wallets


def calculate_risk_indicators(active_wallets: pd.DataFrame) -> pd.DataFrame:
    
    active_wallets['structuring_score'] = 0.0
    mask_struct = active_wallets['snd_tx_count'] >= config.STRUCTURING_MIN_TX
    active_wallets.loc[mask_struct, 'structuring_score'] = (
        active_wallets.loc[mask_struct, 'snd_unique_counterparties'] / 
        (active_wallets.loc[mask_struct, 'snd_tx_count'] + 1)
    ) * np.log1p(active_wallets.loc[mask_struct, 'snd_tx_count'])
    
    active_wallets['passthrough_score'] = 0.0
    active_wallets['flow_ratio'] = np.where(
        active_wallets['rcv_amount_sum'] > 0,
        active_wallets['snd_amount_sum'] / active_wallets['rcv_amount_sum'],
        0
    )
    mask_pass = (
        (active_wallets['flow_ratio'] >= config.PASSTHROUGH_RATIO_MIN) & 
        (active_wallets['flow_ratio'] <= config.PASSTHROUGH_RATIO_MAX) &
        (active_wallets['snd_amount_sum'] > config.PASSTHROUGH_MIN_AMOUNT)
    )
    active_wallets.loc[mask_pass, 'passthrough_score'] = 100.0
    
    active_wallets['bot_score'] = active_wallets['snd_tx_per_minute']
    
    return active_wallets


def process_features(df_tx: pd.DataFrame, df_wallet: pd.DataFrame) -> pd.DataFrame:
    df_tx = engineer_transaction_features(df_tx)
    active_wallets = aggregate_wallet_profiles(df_tx, df_wallet)
    active_wallets = calculate_risk_indicators(active_wallets)
    
    return active_wallets
