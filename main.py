#!/usr/bin/env python3
import pandas as pd
import warnings
import argparse

from src import config
from src.dataset import load_data
from src.features import process_features
from src.modeling.train import train_models
from src.services.risk_engine import (
    calculate_rule_based_scores,
    calculate_final_scores,
    validate_detection,
    export_results,
    get_top_risky_wallets
)
from src.plots import generate_all_plots

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.options.mode.chained_assignment = None


def main(train_mode: bool = True, generate_plots: bool = True):
    print("\n" + "="*70)
    print("CRYPTOTRACE RISK ENGINE - PRODUCTION MODE")
    print("="*70)
    
    df_tx, df_wallet = load_data()
    
    active_wallets = process_features(df_tx, df_wallet)
    
    if train_mode:
        active_wallets, scaler, iso, lof = train_models(active_wallets)
    else:
        from src.modeling.predict import load_models, predict_risk_scores
        scaler, iso, lof = load_models()
        active_wallets = predict_risk_scores(active_wallets, scaler, iso, lof)
    
    active_wallets = calculate_rule_based_scores(active_wallets)
    
    active_wallets = calculate_final_scores(active_wallets)
    
    validation_results = validate_detection(active_wallets)
    
    export_results(active_wallets)
    
    print("\n" + "="*70)
    print(f"TOP {config.TOP_N_WALLETS} HIGHEST RISK WALLETS")
    print("="*70)
    top_wallets = get_top_risky_wallets(active_wallets)
    print(top_wallets[['FINAL_RISK_SCORE', 'Risk_Level', 'snd_tx_count', 
                       'snd_Amount_sum', 'structuring_score', 
                       'passthrough_score', 'bot_score']])
    
    if generate_plots:
        generate_all_plots(active_wallets, save_to_file=True)
    
    print("\n" + "="*70)
    print("RISK ENGINE COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"Total Wallets Analyzed: {len(active_wallets)}")
    print(f"High Risk Wallets: {len(active_wallets[active_wallets['Risk_Level'].isin(['HIGH', 'CRITICAL'])])}")
    print(f"Results saved to: {config.PROCESSED_DATA_DIR}")
    print(f"Plots saved to: {config.FIGURES_DIR}")
    
    return active_wallets, validation_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CryptoTrace Risk Engine")
    parser.add_argument(
        "--mode",
        type=str,
        default="train",
        choices=["train", "predict"],
        help="Mode: 'train' to train new models, 'predict' to use existing models"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating plots"
    )
    
    args = parser.parse_args()
    
    train_mode = args.mode == "train"
    generate_plots = not args.no_plots
    
    active_wallets, validation_results = main(train_mode=train_mode, generate_plots=generate_plots)
