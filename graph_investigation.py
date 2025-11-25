#!/usr/bin/env python3
import pandas as pd
import argparse
import warnings

from src import config
from src.dataset import load_data
from src.features import engineer_transaction_features
from src.graph_analysis import run_graph_investigation

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)


def main(filter_high_risk: bool = True, high_degree_threshold: int = 5):
    print("\n" + "="*70)
    print("CRYPTOTRACE GRAPH INVESTIGATION - PRODUCTION MODE")
    print("="*70)
    
    print("\n[Loading Data]")
    df_tx, df_wallet = load_data()
    df_tx = engineer_transaction_features(df_tx)
    
    risk_scored_path = config.RISK_SCORED_CSV_PATH
    if risk_scored_path.exists():
        print(f"Loading risk-scored wallets from {risk_scored_path}")
        df_wallets_scored = pd.read_csv(risk_scored_path, index_col=0)
    else:
        print("Warning: Risk scoring not found. Run main.py first!")
        print("Proceeding with raw wallet data (no risk filtering)...")
        df_wallets_scored = df_wallet.set_index('Address')
        filter_high_risk = False
    
    df_wallets_with_flags, graph_results = run_graph_investigation(
        df_tx=df_tx,
        df_wallets=df_wallets_scored,
        filter_high_risk=filter_high_risk,
        high_degree_threshold=high_degree_threshold
    )
    
    config.GRAPH_INVESTIGATION_DIR.mkdir(parents=True, exist_ok=True)
    df_wallets_with_flags.to_csv(config.GRAPH_OUTPUT_CSV_PATH)
    print(f"\nUpdated wallet data saved to: {config.GRAPH_OUTPUT_CSV_PATH}")
    
    print("\n" + "="*70)
    print("FLAGGED WALLETS SUMMARY")
    print("="*70)
    print(f"Wash Trading Suspects: {df_wallets_with_flags['wash_trading_flag'].sum()}")
    print(f"Mixer Usage Suspects: {df_wallets_with_flags['mixer_suspect_flag'].sum()}")
    
    if 'Risk_Level' in df_wallets_with_flags.columns:
        high_risk_with_patterns = df_wallets_with_flags[
            (df_wallets_with_flags['Risk_Level'].isin(['HIGH', 'CRITICAL'])) &
            (df_wallets_with_flags['wash_trading_flag'] | df_wallets_with_flags['mixer_suspect_flag'])
        ]
        print(f"\nHIGH/CRITICAL Risk + Pattern Flags: {len(high_risk_with_patterns)}")
        if len(high_risk_with_patterns) > 0:
            print("\nTop Suspects:")
            print(high_risk_with_patterns[['FINAL_RISK_SCORE', 'Risk_Level', 
                                           'wash_trading_flag', 'mixer_suspect_flag']].head(10))
    
    return df_wallets_with_flags, graph_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CryptoTrace Graph Investigation")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all wallets (default: only HIGH/CRITICAL risk)"
    )
    parser.add_argument(
        "--degree-threshold",
        type=int,
        default=None,
        help=f"Minimum degree for hub detection (default: {config.GRAPH_HUB_DEGREE_THRESHOLD})"
    )
    
    args = parser.parse_args()
    
    filter_high_risk = not args.all
    
    df_wallets_with_flags, graph_results = main(
        filter_high_risk=filter_high_risk,
        high_degree_threshold=args.degree_threshold
    )
