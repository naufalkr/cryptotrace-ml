#!/usr/bin/env python3
import pandas as pd
import argparse
import warnings

from src import config
from src.dataset import load_data
from src.features import engineer_transaction_features
from src.graph_analysis import run_graph_investigation
from src.html_report import generate_html_report

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)


def main(filter_high_risk: bool = True, high_degree_threshold: int = 5):
    print("[INFO] Starting graph investigation...")
    
    df_tx, df_wallet = load_data()
    df_tx = engineer_transaction_features(df_tx)
    
    risk_scored_path = config.RISK_SCORED_CSV_PATH
    if risk_scored_path.exists():
        df_wallets_scored = pd.read_csv(risk_scored_path, index_col=0)
    else:
        print("[INFO] Risk scoring not found - using raw wallet data")
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
    
    # Generate interactive HTML report
    html_path = generate_html_report(config.GRAPH_OUTPUT_CSV_PATH)
    
    print(f"[INFO] Results saved to {config.GRAPH_OUTPUT_CSV_PATH}")
    print(f"[INFO] Interactive HTML: {html_path}")
    print(f"[INFO] Wash trading suspects: {df_wallets_with_flags['wash_trading_flag'].sum()}")
    print(f"[INFO] Mixer usage suspects: {df_wallets_with_flags['mixer_suspect_flag'].sum()}")
    
    if 'Risk_Level' in df_wallets_with_flags.columns:
        high_risk_with_patterns = df_wallets_with_flags[
            (df_wallets_with_flags['Risk_Level'].isin(['HIGH', 'CRITICAL'])) &
            (df_wallets_with_flags['wash_trading_flag'] | df_wallets_with_flags['mixer_suspect_flag'])
        ]
        if len(high_risk_with_patterns) > 0:
            print(f"[INFO] HIGH/CRITICAL risk with pattern flags: {len(high_risk_with_patterns)}")
    
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
