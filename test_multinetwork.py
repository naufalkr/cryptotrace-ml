#!/usr/bin/env python3
"""
Test script to verify multi-network data loading (ETH, BSC, Solana)
"""
import pandas as pd
from src.dataset import load_data

print("=" * 80)
print("Testing Multi-Network Data Loading")
print("=" * 80)

try:
    df_tx, df_wallet = load_data()
    
    print("\n" + "=" * 80)
    print("TRANSACTION DATA SUMMARY")
    print("=" * 80)
    print(f"Total transactions: {len(df_tx)}")
    print(f"\nColumns: {list(df_tx.columns)}")
    
    if 'network' in df_tx.columns:
        print(f"\nNetwork breakdown:")
        network_counts = df_tx['network'].value_counts()
        for network, count in network_counts.items():
            print(f"  - {network}: {count} transactions")
    
    print(f"\nFrom addresses (unique): {df_tx['from_address'].nunique()}")
    print(f"To addresses (unique): {df_tx['to_address'].nunique()}")
    
    print(f"\nAmount statistics:")
    print(df_tx['amount'].describe())
    
    print("\n" + "=" * 80)
    print("WALLET DATA SUMMARY")
    print("=" * 80)
    print(f"Total wallets: {len(df_wallet)}")
    print(f"\nColumns: {list(df_wallet.columns)}")
    
    print(f"\nVolume statistics:")
    print(f"  Total volume IN: {df_wallet['total_volume_in'].sum():.4f}")
    print(f"  Total volume OUT: {df_wallet['total_volume_out'].sum():.4f}")
    print(f"  Total transactions: {df_wallet['total_transactions'].sum():.0f}")
    
    print("\n" + "=" * 80)
    print("SAMPLE TRANSACTIONS (first 5)")
    print("=" * 80)
    sample_cols = ['from_address', 'to_address', 'amount', 'fee', 'network']
    available_cols = [col for col in sample_cols if col in df_tx.columns]
    print(df_tx[available_cols].head())
    
    print("\n" + "=" * 80)
    print("✓ SUCCESS: Multi-network data loaded successfully!")
    print("=" * 80)
    print("\nYou can now run:")
    print("  python main.py --mode train")
    print("  python main.py --mode predict")
    
except Exception as e:
    print("\n" + "=" * 80)
    print("✗ ERROR")
    print("=" * 80)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
