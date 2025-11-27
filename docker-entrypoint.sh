#!/bin/bash
set -e

echo "=========================================="
echo "CryptoTrace ML - Docker Container Starting"
echo "=========================================="

# Get environment variables with defaults
LIMIT_TX=${LIMIT_TX:-1000}
BATCH_SIZE=${BATCH_SIZE:-200}
RUN_INTERVAL=${RUN_INTERVAL:-30}

echo "Configuration:"
echo "  Transaction Limit: $LIMIT_TX"
echo "  Batch Size: $BATCH_SIZE"
echo "  Run Interval: $RUN_INTERVAL minutes"
echo ""

# Wait for database to be ready
echo "Waiting for database to be ready..."
until python -c "from src.db import DatabaseConnection; db = DatabaseConnection(); exit(0 if db.connect() and db.disconnect() or True else 1)" 2>/dev/null; do
  echo "  Database is unavailable - sleeping 5s"
  sleep 5
done
echo "✓ Database is ready"
echo ""

# Run initial pipeline execution
echo "Running initial pipeline execution..."
/run-pipeline.sh
echo ""

# Set up cron job for automated runs
echo "Setting up automated pipeline (every $RUN_INTERVAL minutes)..."

# Create cron job
cat > /etc/cron.d/cryptotrace-pipeline << EOF
# CryptoTrace ML Pipeline - Runs every $RUN_INTERVAL minutes
*/$RUN_INTERVAL * * * * root /run-pipeline.sh >> /var/log/cron.log 2>&1

EOF

# Give execution rights
chmod 0644 /etc/cron.d/cryptotrace-pipeline

# Create log file
touch /var/log/cron.log

echo "✓ Cron job configured"
echo ""
echo "=========================================="
echo "CryptoTrace ML - Ready"
echo "Pipeline will run every $RUN_INTERVAL minutes"
echo "=========================================="
echo ""

# Execute the main command (cron or whatever was passed)
if [ "$1" = "cron" ]; then
    # Start cron in foreground and tail the log
    cron && tail -f /var/log/cron.log
else
    # Run the provided command
    exec "$@"
fi
