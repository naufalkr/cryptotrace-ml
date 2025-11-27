import pandas as pd
import json
from typing import List, Dict

from .. import config


def calculate_rule_based_scores(active_wallets: pd.DataFrame) -> pd.DataFrame:

    def calculate_rules(row):
        score = 0

        if row['passthrough_score'] > 0:
            score += config.RULE_LAYERING_SCORE

        if row['structuring_score'] > config.STRUCTURING_HIGH_THRESHOLD:
            score += config.RULE_STRUCTURING_HIGH_SCORE
        elif row['structuring_score'] > config.STRUCTURING_MED_THRESHOLD:
            score += config.RULE_STRUCTURING_MED_SCORE

        if row['bot_score'] > config.BOT_HIGH_VELOCITY:
            score += config.RULE_SPAM_HIGH_SCORE
        elif row['bot_score'] > config.BOT_MED_VELOCITY:
            score += config.RULE_SPAM_MED_SCORE

        if row['snd_amount_sum'] > config.VOLUME_ANOMALY_THRESHOLD:
            score += config.RULE_VOLUME_ANOMALY_SCORE

        return min(score, 100) / 100.0

    active_wallets['risk_score_rule'] = active_wallets.apply(calculate_rules, axis=1)

    return active_wallets


def calculate_final_scores(active_wallets: pd.DataFrame) -> pd.DataFrame:

    active_wallets['risk_score'] = (
        config.ML_WEIGHT * active_wallets['risk_score_ml'] / 100.0 +
        config.RULE_WEIGHT * active_wallets['risk_score_rule']
    )
    active_wallets['risk_score'] = active_wallets['risk_score'].clip(upper=1.0)

    def get_label(s):
        if s >= config.RISK_THRESHOLD_CRITICAL:
            return 'CRITICAL'
        if s >= config.RISK_THRESHOLD_HIGH:
            return 'HIGH'
        if s >= config.RISK_THRESHOLD_MEDIUM:
            return 'MEDIUM'
        return 'LOW'

    active_wallets['risk_level'] = active_wallets['risk_score'].apply(get_label)

    return active_wallets


def validate_detection(active_wallets: pd.DataFrame) -> Dict:
    if not config.VALIDATION_TARGETS:
        return {'validation_skipped': True}

    print("\n[INFO] Validation results:")

    targets = config.VALIDATION_TARGETS
    validation_results = {}

    for target in targets:
        if target in active_wallets.index:
            row = active_wallets.loc[target]
            detected = row['risk_score'] > config.DETECTION_THRESHOLD

            print(f"  {target}: {row['risk_score']:.3f} ({row['risk_level']}) - {'DETECTED' if detected else 'MISSED'}")

            validation_results[target] = {
                'score': row['risk_score'],
                'level': row['risk_level'],
                'detected': detected
            }

    if config.VALIDATION_TARGETS:
        real_wallets = active_wallets[~active_wallets.index.isin(targets)]
    else:
        real_wallets = active_wallets

    high_risk_real = real_wallets[real_wallets['risk_score'] > config.RISK_THRESHOLD_HIGH]
    validation_results['false_positives'] = len(high_risk_real)

    return validation_results


def export_results(active_wallets: pd.DataFrame):
    active_wallets.to_csv(config.RISK_SCORED_CSV_PATH)

    risk_scores = active_wallets[['risk_score', 'risk_level']].to_dict(orient='index')
    with open(config.RISK_SCORED_JSON_PATH, 'w') as f:
        json.dump(risk_scores, f, indent=2)

    print(f"[INFO] Results saved to {config.REPORTS_DIR}/risk_scoring/")


def get_top_risky_wallets(active_wallets: pd.DataFrame, n: int = None) -> pd.DataFrame:
    if n is None:
        n = config.TOP_N_WALLETS

    return active_wallets.sort_values(by="risk_score", ascending=False).head(n)
