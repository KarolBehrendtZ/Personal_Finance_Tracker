#!/bin/bash

# Database backup script

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="finance_tracker_backup_${TIMESTAMP}.sql"

echo "📦 Creating database backup..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
docker-compose exec -T postgres pg_dump -U postgres finance_tracker > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress the backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_FILE}.gz"

# Keep only the last 10 backups
echo "🧹 Cleaning up old backups..."
ls -t ${BACKUP_DIR}/finance_tracker_backup_*.sql.gz | tail -n +11 | xargs -r rm

echo "✅ Backup completed successfully!"
