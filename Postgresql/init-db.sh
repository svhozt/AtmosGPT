#!/bin/bash

# Wait for PostgreSQL to start
echo "Waiting for postgres..."

# Restore the database from the dump in the new location
pg_restore -U postgres -d bremengeo /custom_backup/backup.sql
