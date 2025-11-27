#!/bin/bash
set -e

# Get environment variables with defaults
LIMIT_TX=${LIMIT_TX:-1000}
BATCH_SIZE=${BATCH_SIZE:-200}

# Timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=========================================="
echo "[$TIMESTAMP] CryptoTrace ML Pipeline Started"
echo "=========================================="

cd /app

# Step 1: Collect data from database
echo ""
echo "Step 1: Collecting data from database..."
echo "Command: python collect_data.py --limit-tx $LIMIT_TX"
if python collect_data.py --limit-tx $LIMIT_TX; then
    echo "✓ Data collection completed"
else
    echo "✗ Data collection failed"
    exit 1
fi

# Step 2: Run risk scoring analysis
echo ""
echo "Step 2: Running risk scoring analysis..."
echo "Command: python main.py --mode predict --no-plots"
if python main.py --mode predict --no-plots; then
    echo "✓ Risk scoring completed"
else
    echo "✗ Risk scoring failed"
    exit 1
fi

# Step 3: Update database with risk scores
echo ""
echo "Step 3: Updating database with risk scores..."
echo "Command: python update_risk_scores.py --batch-size $BATCH_SIZE"
if echo "yes" | python update_risk_scores.py --batch-size $BATCH_SIZE; then
    echo "✓ Database update completed"
else
    echo "✗ Database update failed"
    exit 1
fi

# Completion
TIMESTAMP_END=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "=========================================="
echo "[$TIMESTAMP_END] Pipeline Completed Successfully"
echo "=========================================="
echo ""
