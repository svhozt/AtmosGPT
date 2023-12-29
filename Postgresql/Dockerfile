# Use the official PostgreSQL image as a parent image
FROM postgres:latest

# Install PostGIS and pgRouting
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgis postgresql-16-postgis-3 \
    && apt-get install -y --no-install-recommends postgresql-16-pgrouting

# Copy the custom format backup file into a different directory inside the container
COPY backup.sql /custom_backup/backup.sql
COPY init-db.sh /docker-entrypoint-initdb.d/
