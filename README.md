# ELISP CryptoTrace ML

Machine Learning & Analytics for Cryptocurrency Investigation

## Installation

```bash
pip install -e .
```

## Usage

### Risk Scoring

Train models and analyze wallet risk:

```bash
python main.py --mode train
```

Use existing models for prediction:

```bash
python main.py --mode predict
```

Skip visualization generation:

```bash
python main.py --mode train --no-plots
```

**Outputs:**
- `reports/risk_scoring/wallet_risk_scored_final.csv` - Risk scores and levels per wallet
- `reports/risk_scoring/risk_scores_final.json` - JSON format scores
- `reports/risk_scoring/figures/*.png` - Distribution, pie chart, top wallets, correlations

### Graph Investigation

Analyze transaction networks and detect patterns:

```bash
# Analyze HIGH/CRITICAL risk wallets only
python graph_investigation.py

# Analyze all wallets
python graph_investigation.py --all

# Adjust hub detection threshold
python graph_investigation.py --degree-threshold 10
```

**Outputs:**
- `reports/graph_investigation/wallet_with_graph_flags.csv` - Wallets with wash trading and mixer flags
- `reports/graph_investigation/investigation_graph_final.png` - Network visualization

### Workflow

```
Step 1: Risk Scoring          Step 2: Graph Analysis
python main.py         -->     python graph_investigation.py
```

## Features

### Risk Scoring Engine
- ML-based anomaly detection (IsolationForest, LocalOutlierFactor)
- Rule-based pattern detection (structuring, layering, bot behavior)
- Hybrid scoring (30% ML + 70% Rules)
- Automatic bad actor detection validation

### Graph Analysis
- Transaction network topology analysis
- Community detection (Louvain algorithm)
- Wash trading cycle detection
- Mixer usage pattern identification
- Hub wallet identification

### Pattern Detection
- Smurfing: Multiple small transactions to avoid thresholds
- Layering: Quick passthrough transactions to obscure origin
- Bot behavior: High-velocity transaction patterns
- Round number deposits: Potential mixer usage

## Configuration

All parameters configurable in `src/config.py`:

**Risk Scoring:**
- `RISK_THRESHOLD_CRITICAL = 75`
- `RISK_THRESHOLD_HIGH = 50`
- `ML_WEIGHT = 0.3` / `RULE_WEIGHT = 0.7`

**Graph Analysis:**
- `GRAPH_HUB_DEGREE_THRESHOLD = 5`
- `GRAPH_CYCLE_MAX_LENGTH = 3`
- `ROUND_AMOUNTS = [0.1, 0.5, 1.0, 5.0, 10.0, ...]`

## Data Structure

```
data/raw/               # Input transaction and wallet data
models/                 # Trained ML models (.joblib)
reports/
  risk_scoring/         # Risk analysis outputs
    figures/            # Visualization charts
  graph_investigation/  # Network analysis outputs
```

## Requirements

- Python 3.11+
- pandas, numpy, scikit-learn
- networkx, python-louvain
- matplotlib, seaborn
