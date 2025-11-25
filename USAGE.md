# CryptoTrace ML - Usage Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Run the Risk Engine

#### Training Mode (Train new models)
```bash
python main.py --mode train
```

#### Prediction Mode (Use existing models)
```bash
python main.py --mode predict
```

#### Skip Plot Generation
```bash
python main.py --mode train --no-plots
```

## 📂 Project Structure

```
elisp-cryptotrace-ml/
├── main.py                      # Main entry point
├── src/
│   ├── config.py               # All configurations
│   ├── dataset.py              # Data loading & synthetic injection
│   ├── features.py             # Feature engineering
│   ├── plots.py                # Visualization functions
│   ├── modeling/
│   │   ├── train.py           # ML model training
│   │   └── predict.py         # ML model inference
│   └── services/
│       └── risk_engine.py     # Risk scoring & validation
├── data/
│   ├── raw/                   # Input data (transaction.json, wallet.json)
│   └── processed/             # Output results
├── models/                    # Trained ML models (.joblib)
└── reports/
    └── figures/              # Generated plots
```

## ⚙️ Configuration

Edit `src/config.py` to customize:

### Data Paths
```python
TRANSACTION_JSON_PATH = RAW_DATA_DIR / "transaction.json"
WALLET_JSON_PATH = RAW_DATA_DIR / "wallet.json"
```

### Synthetic Injection
```python
INJECT_SYNTHETIC_DATA = True  # Set False to disable

SMURFING_TX_COUNT = 50
SMURFING_AMOUNT = 2.0

LAYERING_AMOUNT_IN = 500.0
LAYERING_AMOUNT_OUT = 499.5

SPAM_TX_COUNT = 100
```

### ML Parameters
```python
MIN_TX_FOR_ML = 2              # Minimum transactions for ML
ISO_CONTAMINATION = 0.05        # IsolationForest contamination
LOF_N_NEIGHBORS = 20           # LOF neighbors
```

### Risk Scoring Rules
```python
RULE_LAYERING_SCORE = 80
RULE_STRUCTURING_HIGH_SCORE = 60
RULE_SPAM_HIGH_SCORE = 50
VOLUME_ANOMALY_THRESHOLD = 100.0

ML_WEIGHT = 0.3                # 30% ML
RULE_WEIGHT = 0.7              # 70% Rule-based
```

## 📊 Output Files

### 1. Risk Scores (CSV)
Location: `data/processed/wallet_risk_scored_final.csv`

Columns:
- `FINAL_RISK_SCORE` - Final risk score (0-100)
- `Risk_Level` - CRITICAL / HIGH / MEDIUM / LOW
- `snd_tx_count` - Number of sent transactions
- `snd_Amount_sum` - Total amount sent
- `structuring_score` - Smurfing detection score
- `passthrough_score` - Layering detection score
- `bot_score` - Bot/spam detection score

### 2. Risk Scores (JSON)
Location: `data/processed/risk_scores_final.json`

### 3. ML Models
Location: `models/`
- `isolation_forest.joblib` - IsolationForest model
- `local_outlier_factor.joblib` - LOF model
- `scaler.joblib` - RobustScaler

### 4. Visualizations
Location: `reports/figures/`
- `risk_distribution.png` - Histogram of risk scores
- `risk_level_pie.png` - Pie chart of risk levels
- `top_risky_wallets.png` - Bar chart of top risky wallets
- `tx_vs_risk.png` - Scatter plot: transactions vs risk
- `correlation_heatmap.png` - Feature correlation heatmap

## 🔍 Understanding the Results

### Risk Levels
- **CRITICAL (≥75)**: High confidence malicious activity detected
- **HIGH (≥50)**: Suspicious patterns detected
- **MEDIUM (≥25)**: Minor anomalies detected
- **LOW (<25)**: Normal activity

### Detection Scenarios

#### 1. Smurfing (Structuring)
- **Pattern**: One sender → Many receivers
- **Indicator**: `structuring_score` > 2.0
- **Example**: 50 transactions to 50 different wallets

#### 2. Layering (Money Mule)
- **Pattern**: Money in → Money out quickly (1:1 ratio)
- **Indicator**: `passthrough_score` = 100
- **Example**: Receive 500 ETH, send 499.5 ETH in 30 seconds

#### 3. Spam/Bot Activity
- **Pattern**: High velocity transactions
- **Indicator**: `bot_score` > 20 tx/minute
- **Example**: 100 transactions in 8 minutes

## 🛠️ Advanced Usage

### Use Your Own Data

1. Place your data in `data/raw/`:
   - `transaction.json` or `transaction.csv`
   - `wallet.json` or `wallet.csv`

2. Disable synthetic injection in `config.py`:
```python
INJECT_SYNTHETIC_DATA = False
```

3. Run the engine:
```bash
python main.py --mode train
```

### Programmatic Usage

```python
from src.dataset import load_data
from src.features import process_features
from src.modeling.train import train_models
from src.services.risk_engine import (
    calculate_rule_based_scores,
    calculate_final_scores,
    get_top_risky_wallets
)

# Load data
df_tx, df_wallet = load_data()

# Process features
active_wallets = process_features(df_tx, df_wallet)

# Train models
active_wallets, scaler, iso, lof = train_models(active_wallets)

# Calculate scores
active_wallets = calculate_rule_based_scores(active_wallets)
active_wallets = calculate_final_scores(active_wallets)

# Get top risky wallets
top_30 = get_top_risky_wallets(active_wallets, n=30)
print(top_30)
```

### Custom Risk Rules

Edit `src/services/risk_engine.py` → `calculate_rules()` function:

```python
def calculate_rules(row):
    score = 0
    
    # Add your custom rule here
    if row['snd_Amount_sum'] > 1000:  # Whale activity
        score += 40
    
    if row['passthrough_score'] > 0:
        score += 80
    
    return min(score, 100)
```

## 📈 Performance Tips

1. **Large datasets**: Increase `MIN_TX_FOR_ML` to reduce computation
2. **Better detection**: Adjust contamination rates in config
3. **Faster processing**: Disable plots with `--no-plots`

## 🐛 Troubleshooting

### Models not found
Run in training mode first:
```bash
python main.py --mode train
```

### Memory issues
Reduce dataset size or increase `MIN_TX_FOR_ML` threshold

### False positives
Adjust rule weights in `config.py`:
- Decrease `RULE_WEIGHT`
- Increase `ML_WEIGHT`

## 📧 Support

For issues or questions, contact: Nathan Kho Pancras (ELISP Team)
