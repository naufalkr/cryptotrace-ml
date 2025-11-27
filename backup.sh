#!/bin/bash
# Backup script for CryptoTrace ML

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

echo "========================================"
echo "CryptoTrace ML - Backup Script"
echo "========================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Backing up PostgreSQL database..."
docker-compose exec -T postgres pg_dump -U postgres cryptotrace > "$BACKUP_DIR/cryptotrace_db_$TIMESTAMP.sql"
echo "✓ Database backed up: $BACKUP_DIR/cryptotrace_db_$TIMESTAMP.sql"

# Backup models
echo ""
echo "Backing up models..."
if [ -d "./models" ] && [ "$(ls -A ./models)" ]; then
    tar czf "$BACKUP_DIR/models_$TIMESTAMP.tar.gz" ./models
    echo "✓ Models backed up: $BACKUP_DIR/models_$TIMESTAMP.tar.gz"
else
    echo "⚠ No models to backup"
fi

# Backup data
echo ""
echo "Backing up data files..."
if [ -d "./data" ] && [ "$(ls -A ./data)" ]; then
    tar czf "$BACKUP_DIR/data_$TIMESTAMP.tar.gz" ./data
    echo "✓ Data backed up: $BACKUP_DIR/data_$TIMESTAMP.tar.gz"
else
    echo "⚠ No data to backup"
fi

# Backup reports
echo ""
echo "Backing up reports..."
if [ -d "./reports" ] && [ "$(ls -A ./reports)" ]; then
    tar czf "$BACKUP_DIR/reports_$TIMESTAMP.tar.gz" ./reports
    echo "✓ Reports backed up: $BACKUP_DIR/reports_$TIMESTAMP.tar.gz"
else
    echo "⚠ No reports to backup"
fi

# Clean old backups
echo ""
echo "Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.sql" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "✓ Old backups cleaned"

# Summary
echo ""
echo "========================================"
echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo "========================================"
echo ""
echo "To restore:"
echo "  Database: cat $BACKUP_DIR/cryptotrace_db_$TIMESTAMP.sql | docker-compose exec -T postgres psql -U postgres cryptotrace"
echo "  Models:   tar xzf $BACKUP_DIR/models_$TIMESTAMP.tar.gz"
echo "  Data:     tar xzf $BACKUP_DIR/data_$TIMESTAMP.tar.gz"
echo "  Reports:  tar xzf $BACKUP_DIR/reports_$TIMESTAMP.tar.gz"
echo ""
