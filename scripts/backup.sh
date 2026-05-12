#!/bin/bash

# Database backup script for LexChain Sovereign

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lexchain_backup_${TIMESTAMP}"

mkdir -p $BACKUP_DIR

echo "🔷 LexChain Database Backup"
echo "============================"

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Attempting default..."
    export DATABASE_URL="postgresql://lexchain:password@localhost:5432/lexchain"
fi

echo "Creating backup: $BACKUP_NAME"

if command -v docker &> /dev/null; then
    docker exec lexchain-postgres-1 pg_dump -U lexchain lexchain > "${BACKUP_DIR}/${BACKUP_NAME}.sql"
else
    echo "Docker not available. Please run pg_dump manually:"
    echo "  pg_dump -h localhost -U lexchain lexchain > ${BACKUP_DIR}/${BACKUP_NAME}.sql"
fi

if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.sql" ]; then
    gzip "${BACKUP_DIR}/${BACKUP_NAME}.sql"
    echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
    
    find $BACKUP_DIR -name "lexchain_backup_*.sql.gz" -mtime +7 -delete
    echo "🗑️  Old backups (>7 days) cleaned up"
else
    echo "❌ Backup failed"
    exit 1
fi

echo ""
echo "Backup complete: ${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"