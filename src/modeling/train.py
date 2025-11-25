import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from typing import Tuple

from .. import config


def train_models(active_wallets: pd.DataFrame) -> Tuple[pd.DataFrame, RobustScaler, IsolationForest, LocalOutlierFactor]:
    print("\n[ML] Training models...")
    
    ml_subset = active_wallets[active_wallets['snd_tx_count'] >= config.MIN_TX_FOR_ML].copy()
    
    if len(ml_subset) <= 5:
        print(f"   - Not enough data for ML ({len(ml_subset)} wallets). Skipping ML training.")
        active_wallets['risk_score_ml'] = 0
        return active_wallets, None, None, None
    
    print(f"   - Training on {len(ml_subset)} wallets")
    
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(ml_subset[config.ML_FEATURES])
    
    iso = IsolationForest(
        contamination=config.ISO_CONTAMINATION,
        random_state=config.ISO_RANDOM_STATE
    )
    iso.fit(X_scaled)
    raw_iso = iso.score_samples(X_scaled)
    
    lof = LocalOutlierFactor(
        n_neighbors=min(config.LOF_N_NEIGHBORS, len(ml_subset)-1),
        contamination=config.LOF_CONTAMINATION
    )
    lof.fit_predict(X_scaled)
    raw_lof = lof.negative_outlier_factor_
    
    def normalize_scores(s):
        return ((s.max() - s) / (s.max() - s.min() + 1e-10)) * 100
    
    ml_subset['risk_score_ml'] = (normalize_scores(raw_iso) + normalize_scores(raw_lof)) / 2
    active_wallets = active_wallets.join(ml_subset[['risk_score_ml']], how='left')
    active_wallets['risk_score_ml'] = active_wallets['risk_score_ml'].fillna(0)
    
    joblib.dump(scaler, config.SCALER_PATH)
    joblib.dump(iso, config.ISOLATION_FOREST_MODEL_PATH)
    joblib.dump(lof, config.LOF_MODEL_PATH)
    
    print(f"   - Models saved to {config.MODELS_DIR}")
    
    return active_wallets, scaler, iso, lof
