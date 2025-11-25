import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from typing import Tuple

from .. import config


def train_models(active_wallets: pd.DataFrame) -> Tuple[pd.DataFrame, RobustScaler, IsolationForest, LocalOutlierFactor]:
    print("[INFO] Training ML models...")
    
    train_data = active_wallets.copy()
    if config.VALIDATION_TARGETS:
        train_data = train_data[~train_data.index.isin(config.VALIDATION_TARGETS)]
    
    ml_subset = train_data[train_data['snd_tx_count'] >= config.MIN_TX_FOR_ML].copy()
    
    if len(ml_subset) <= 5:
        print("[WARN] Not enough data for ML training")
        active_wallets['risk_score_ml'] = 0
        return active_wallets, None, None, None
    
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
    
    all_ml_data = active_wallets[active_wallets['snd_tx_count'] >= config.MIN_TX_FOR_ML].copy()
    X_all_scaled = scaler.transform(all_ml_data[config.ML_FEATURES])
    
    raw_iso_all = iso.score_samples(X_all_scaled)
    lof_all = LocalOutlierFactor(
        n_neighbors=min(config.LOF_N_NEIGHBORS, len(all_ml_data)-1),
        contamination=config.LOF_CONTAMINATION
    )
    lof_all.fit_predict(X_all_scaled)
    raw_lof_all = lof_all.negative_outlier_factor_
    
    all_ml_data['risk_score_ml'] = (normalize_scores(raw_iso_all) + normalize_scores(raw_lof_all)) / 2
    
    active_wallets = active_wallets.join(all_ml_data[['risk_score_ml']], how='left')
    active_wallets['risk_score_ml'] = active_wallets['risk_score_ml'].fillna(0)
    
    joblib.dump(scaler, config.SCALER_PATH)
    joblib.dump(iso, config.ISOLATION_FOREST_MODEL_PATH)
    joblib.dump(lof, config.LOF_MODEL_PATH)
    
    return active_wallets, scaler, iso, lof
