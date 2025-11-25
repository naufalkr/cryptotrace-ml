from pathlib import Path

# ============================================================================
# PATH CONFIGURATION - Lokasi file input/output dan model
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
RISK_SCORING_DIR = REPORTS_DIR / "risk_scoring"
GRAPH_INVESTIGATION_DIR = REPORTS_DIR / "graph_investigation"

for dir_path in [RAW_DATA_DIR, MODELS_DIR, REPORTS_DIR, RISK_SCORING_DIR, GRAPH_INVESTIGATION_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

TRANSACTION_JSON_PATH = RAW_DATA_DIR / "transaction.json"
WALLET_JSON_PATH = RAW_DATA_DIR / "wallet.json"

RISK_SCORED_CSV_PATH = RISK_SCORING_DIR / "wallet_risk_scored_final.csv"
RISK_SCORED_JSON_PATH = RISK_SCORING_DIR / "risk_scores_final.json"
RISK_FIGURES_DIR = RISK_SCORING_DIR / "figures"

GRAPH_OUTPUT_CSV_PATH = GRAPH_INVESTIGATION_DIR / "wallet_with_graph_flags.csv"
GRAPH_OUTPUT_PNG_PATH = GRAPH_INVESTIGATION_DIR / "investigation_graph_final.png"

ISOLATION_FOREST_MODEL_PATH = MODELS_DIR / "isolation_forest.joblib"
LOF_MODEL_PATH = MODELS_DIR / "local_outlier_factor.joblib"
SCALER_PATH = MODELS_DIR / "scaler.joblib"





# ============================================================================
# VALIDATION CONFIGURATION - Data sintetis untuk testing deteksi
# ============================================================================
# Set INJECT_SYNTHETIC_DATA=False untuk production dengan data asli saja
INJECT_SYNTHETIC_DATA = True

# Set TRAIN_ON_CLEAN_DATA=True agar model tidak dilatih dengan validation targets
TRAIN_ON_CLEAN_DATA = True

# Nama wallet sintetis untuk validasi
ACTOR_SMURF = "0xBAD_ACTOR_SMURFING"
ACTOR_LAYER = "0xBAD_ACTOR_LAYERING"
ACTOR_SPAM = "0xBAD_ACTOR_SPAMMER"

# Parameter smurfing: transaksi kecil berulang-ulang
SMURFING_TX_COUNT = 50
SMURFING_AMOUNT = 2.0
SMURFING_INTERVAL_SECONDS = 10

# Parameter layering: in besar, out cepat dengan jumlah hampir sama
LAYERING_AMOUNT_IN = 500.0
LAYERING_AMOUNT_OUT = 499.5
LAYERING_TIME_DIFF_SECONDS = 30

# Parameter spam: transaksi sangat kecil dengan frekuensi tinggi
SPAM_TX_COUNT = 100
SPAM_AMOUNT = 0.001
SPAM_INTERVAL_SECONDS = 5

# List wallet untuk validasi - kosongkan untuk production
VALIDATION_TARGETS = [
    ACTOR_SMURF,
    ACTOR_LAYER,
    ACTOR_SPAM
]





# ============================================================================
# MACHINE LEARNING CONFIGURATION - Parameter model anomaly detection
# ============================================================================
ML_FEATURES = [
    'snd_tx_count',
    'snd_Amount_sum',
    'snd_unique_counterparties',
    'structuring_score',
    'passthrough_score',
    'bot_score'
]

MIN_TX_FOR_ML = 2

# Isolation Forest parameters
ISO_CONTAMINATION = 0.05
ISO_RANDOM_STATE = 42

# Local Outlier Factor parameters
LOF_N_NEIGHBORS = 20
LOF_CONTAMINATION = 0.05







# ============================================================================
# RISK SCORING CONFIGURATION - Threshold dan bobot untuk risk score
# ============================================================================
# Risk level thresholds
RISK_THRESHOLD_CRITICAL = 75
RISK_THRESHOLD_HIGH = 50
RISK_THRESHOLD_MEDIUM = 25

# Rule-based scoring weights
RULE_LAYERING_SCORE = 80
RULE_STRUCTURING_HIGH_SCORE = 60
RULE_STRUCTURING_MED_SCORE = 30
RULE_SPAM_HIGH_SCORE = 50
RULE_SPAM_MED_SCORE = 20
RULE_VOLUME_ANOMALY_SCORE = 20

# Structuring detection thresholds
STRUCTURING_MIN_TX = 5
STRUCTURING_HIGH_THRESHOLD = 2.0
STRUCTURING_MED_THRESHOLD = 1.0

# Passthrough (layering) detection parameters
PASSTHROUGH_RATIO_MIN = 0.9
PASSTHROUGH_RATIO_MAX = 1.1
PASSTHROUGH_MIN_AMOUNT = 10.0

# Bot/spam detection thresholds
BOT_HIGH_VELOCITY = 20
BOT_MED_VELOCITY = 5

# Volume anomaly threshold
VOLUME_ANOMALY_THRESHOLD = 100.0

# Final score weights: 30% ML + 70% Rule-based
ML_WEIGHT = 0.3
RULE_WEIGHT = 0.7

# Detection threshold untuk validation
DETECTION_THRESHOLD = 60






# ============================================================================
# VISUALIZATION CONFIGURATION - Parameter untuk plot dan grafik
# ============================================================================
TOP_N_WALLETS = 30

# Threshold untuk menentukan hub (wallet dengan banyak koneksi)
GRAPH_HUB_DEGREE_THRESHOLD = 5

# Threshold untuk menampilkan label di grafik
GRAPH_LABEL_DEGREE_THRESHOLD = 20

# Panjang maksimal cycle untuk wash trading detection
GRAPH_CYCLE_MAX_LENGTH = 3

# Round amounts untuk mixer detection
ROUND_AMOUNTS = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]
