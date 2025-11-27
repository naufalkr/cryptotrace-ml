#!/usr/bin/env python3
import pandas as pd
import numpy as np
from src.dataset import load_data
from src.features import process_features
from src.modeling.train import train_models
from src.services.risk_engine import calculate_rule_based_scores, calculate_final_scores

df_tx, df_wallet = load_data()

print('\n' + '='*80)
print('[1] TRANSACTION DATA ANALYSIS')
print('='*80)
print(f'Total transactions: {len(df_tx)}')
print(f'Unique senders: {df_tx["from_address"].nunique()}')
print(f'Unique receivers: {df_tx["to_address"].nunique()}')
print(f'\nAmount distribution (in ETH):')
print(df_tx['amount'].describe())
print(f'\nFee distribution (in ETH):')
print(df_tx['fee'].describe())
print(f'\nTime range: {df_tx["block_time"].min()} to {df_tx["block_time"].max()}')
print(f'Transactions per unique sender:')
print(df_tx['from_address'].value_counts().describe())

print('\n' + '='*80)
print('[2] WALLET DATA ANALYSIS')
print('='*80)
print(f'Total wallets in DB: {len(df_wallet)}')
print(f'Wallets with activity: {(df_wallet["total_transactions"] > 0).sum()}')
print(f'\nVolume IN distribution:')
print(df_wallet['total_volume_in'].describe())
print(f'\nVolume OUT distribution:')
print(df_wallet['total_volume_out'].describe())

active_wallets = process_features(df_tx, df_wallet)

print('\n' + '='*80)
print('[3] ACTIVE WALLETS (after feature engineering)')
print('='*80)
print(f'Active wallets: {len(active_wallets)}')
print(f'Wallets with snd_tx_count >= 1: {(active_wallets["snd_tx_count"] >= 1).sum()}')
print(f'Wallets with snd_tx_count >= 2 (MIN_TX_FOR_ML): {(active_wallets["snd_tx_count"] >= 2).sum()}')
print(f'\nsnd_tx_count distribution:')
print(active_wallets['snd_tx_count'].describe())

print('\n' + '='*80)
print('[4] FEATURE ENGINEERING QUALITY')
print('='*80)
print('\nSending features:')
print(f'  snd_amount_sum range: {active_wallets["snd_amount_sum"].min():.4f} to {active_wallets["snd_amount_sum"].max():.4f}')
print(f'  snd_unique_counterparties range: {active_wallets["snd_unique_counterparties"].min()} to {active_wallets["snd_unique_counterparties"].max()}')

print('\nStructuring Score (tx diversity indicator):')
print(active_wallets['structuring_score'].describe())
print(f'  Non-zero scores: {(active_wallets["structuring_score"] > 0).sum()}')

print('\nPassthrough Score (layering indicator):')
print(active_wallets['passthrough_score'].describe())
print(f'  Detected suspicious (>0): {(active_wallets["passthrough_score"] > 0).sum()}')

print('\nBot Score (velocity indicator):')
print(active_wallets['bot_score'].describe())

print('\nReceiving features:')
print(f'  rcv_tx_count max: {active_wallets["rcv_tx_count"].max()}')
print(f'  rcv_amount_sum max: {active_wallets["rcv_amount_sum"].max():.4f}')

print('\n' + '='*80)
print('[5] ML MODEL TRAINING')
print('='*80)
ml_before = active_wallets.copy()
active_wallets, scaler, iso, lof = train_models(active_wallets)
print(f'\nML Feature subset for training:')
wallets_for_ml = active_wallets[active_wallets['snd_tx_count'] >= 2]
print(f'  Wallets used for ML training: {len(wallets_for_ml)}')
print(f'  % of active wallets: {len(wallets_for_ml)/len(active_wallets)*100:.1f}%')

print(f'\nML Anomaly Scores:')
print(active_wallets['risk_score_ml'].describe())
print(f'  High anomaly (>50): {(active_wallets["risk_score_ml"] > 50).sum()}')
print(f'  Very high anomaly (>75): {(active_wallets["risk_score_ml"] > 75).sum()}')

print('\n' + '='*80)
print('[6] RULE-BASED SCORING')
print('='*80)
active_wallets = calculate_rule_based_scores(active_wallets)
print(f'\nRule-based scores distribution:')
print(active_wallets['risk_score_rule'].describe())

print(f'\nRule detection breakdown:')
print(f'  Layering detected: {(active_wallets["passthrough_score"] > 0).sum()}')
print(f'  High structuring: {((active_wallets["structuring_score"] > 2.0)).sum()}')
print(f'  Medium structuring: {((active_wallets["structuring_score"] > 1.0) & (active_wallets["structuring_score"] <= 2.0)).sum()}')
print(f'  High velocity bots: {(active_wallets["bot_score"] > 20).sum()}')

print('\n' + '='*80)
print('[7] FINAL RISK SCORES (30% ML + 70% RULES)')
print('='*80)
active_wallets = calculate_final_scores(active_wallets)
print(f'\nFinal score distribution:')
print(active_wallets['risk_score'].describe())

print(f'\nRisk Level Distribution:')
risk_dist = active_wallets['risk_level'].value_counts()
for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    count = risk_dist.get(level, 0)
    pct = (count / len(active_wallets)) * 100
    print(f'  {level}: {count} wallets ({pct:.1f}%)')

print('\n' + '='*80)
print('[8] TOP 10 WALLETS')
print('='*80)
top10 = active_wallets.nlargest(10, 'risk_score')
print(f"\n{'Rank':<5} {'Address':<16} {'Risk':<6} {'Level':<10} {'TX':<4} {'Amount':<12} {'Struct':<8} {'Passth':<8} {'Bot':<8} {'ML%':<6} {'Rule%':<6}")
print('-'*110)
for idx, (addr, row) in enumerate(top10.iterrows(), 1):
    print(f"{idx:<5} {str(addr)[:16]:<16} {row['risk_score']:<6.1f} {row['risk_level']:<10} {int(row['snd_tx_count']):<4} {row['snd_amount_sum']:<12.4f} {row['structuring_score']:<8.2f} {row['passthrough_score']:<8.2f} {row['bot_score']:<8.2f} {row['risk_score_ml']:<6.1f} {row['risk_score_rule']:<6.1f}")

print('\n' + '='*80)
print('[9] VALIDATION TARGETS (SYNTHETIC BAD ACTORS)')
print('='*80)
validation_targets = ['0xBAD_ACTOR_SMURFING', '0xBAD_ACTOR_LAYERING', '0xBAD_ACTOR_SPAMMER']
for target in validation_targets:
    if target in active_wallets.index:
        row = active_wallets.loc[target]
        detected = 'YES' if row['risk_score'] > 60 else 'NO'
        print(f'\n{target}:')
        print(f'  ML Score: {row["risk_score_ml"]:.1f}')
        print(f'  Rule Score: {row["risk_score_rule"]:.1f}')
        print(f'  Final Score: {row["risk_score"]:.1f}')
        print(f'  Risk Level: {row["risk_level"]}')
        print(f'  Detected (>60)?: {detected}')
        print(f'  TX Count: {int(row["snd_tx_count"])}')
        print(f'  Amount Sum: {row["snd_amount_sum"]:.4f}')
