import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Optional

from .. import config


def load_models():
    if not config.SCALER_PATH.exists():
        print("[INFO] Models not found. Please train models first.")
        return None, None, None
    
    scaler = joblib.load(config.SCALER_PATH)
    iso = joblib.load(config.ISOLATION_FOREST_MODEL_PATH)
    lof = joblib.load(config.LOF_MODEL_PATH)
    
    print("[INFO] Models loaded from disk")
    return scaler, iso, lof


def predict_risk_scores(active_wallets: pd.DataFrame, scaler=None, iso=None, lof=None) -> pd.DataFrame:
    if scaler is None or iso is None or lof is None:
        active_wallets['risk_score_ml'] = 0
        return active_wallets
    
    ml_subset = active_wallets[active_wallets['snd_tx_count'] >= config.MIN_TX_FOR_ML].copy()
    
    if len(ml_subset) == 0:
        active_wallets['risk_score_ml'] = 0
        return active_wallets
    
    X_scaled = scaler.transform(ml_subset[config.ML_FEATURES])
    
    raw_iso = iso.score_samples(X_scaled)
    
    from sklearn.neighbors import LocalOutlierFactor
    lof_temp = LocalOutlierFactor(
        n_neighbors=min(config.LOF_N_NEIGHBORS, len(ml_subset)-1),
        contamination=config.LOF_CONTAMINATION,
        novelty=False
    )
    lof_temp.fit_predict(X_scaled)
    raw_lof = lof_temp.negative_outlier_factor_
    
    def normalize_scores(s):
        return ((s.max() - s) / (s.max() - s.min() + 1e-10)) * 100
    
    ml_subset['risk_score_ml'] = (normalize_scores(raw_iso) + normalize_scores(raw_lof)) / 2
    active_wallets = active_wallets.join(ml_subset[['risk_score_ml']], how='left')
    active_wallets['risk_score_ml'] = active_wallets['risk_score_ml'].fillna(0)
    
    return active_wallets
