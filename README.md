# ELISP CryptoTrace ML

Machine Learning & Analytics for Cryptocurrency Investigation

## Installation

### Option 1: Docker (Recommended) 🐳

**Quick Start:**
```bash
# Setup and start
make setup
make up

# Or manual
cp .env.docker .env
nano .env  # Edit DB_PASSWORD
docker-compose up -d --build
```

**Automated Pipeline:**
- Runs every 30 minutes automatically
- Collects data → Risk scoring → Updates database
- Monitor with: `make logs`

**Common Commands:**
```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
make logs          # View logs
make pipeline      # Run manually
make shell         # Open container shell
make backup-db     # Backup database
```

📖 **Dokumentasi lengkap**: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | [DOCKER.md](DOCKER.md)

### Option 2: Local Installation

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

### Update Database with Risk Scores

After risk scoring analysis, update the database with calculated risk scores:

```bash
# Preview updates without modifying database
python update_risk_scores.py --dry-run

# Update database (will prompt for confirmation)
python update_risk_scores.py

# Update with custom batch size
python update_risk_scores.py --batch-size 500

# Update from custom input file
python update_risk_scores.py --input custom_scores.json
```

**Features:**
- Bulk updates wallet_addresses table with risk_score and risk_level
- Batch processing for efficient updates
- Dry-run mode for previewing changes
- Confirmation prompt before live updates
- Progress tracking during update

### Workflow

```
Step 1: Data Collection              Step 2: Risk Scoring              Step 3: Update Database              Step 4: Graph Analysis
python collect_data.py       -->     python main.py            -->     python update_risk_scores.py  -->  python graph_investigation.py
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
