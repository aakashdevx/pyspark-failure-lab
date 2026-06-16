#!/bin/bash
# ================================================================
# Hive Metastore Entrypoint
# Initializes Derby schema on first run
# Starts Thrift metastore server on port 9083
# ================================================================

set -eo pipefail

METASTORE_HOME=${METASTORE_HOME:-/opt/hive-metastore}

echo "Starting Hive Metastore..."
echo "  METASTORE_HOME : ${METASTORE_HOME}"
echo "  METASTORE_PORT : ${METASTORE_PORT:-9083}"

# Initialize schema if Derby DB does not exist yet
if [ ! -d "${METASTORE_HOME}/data/metastore_db" ]; then
    echo "First run detected — initializing Derby schema..."
    ${METASTORE_HOME}/bin/schematool \
        -initSchema \
        -dbType derby \
        -verbose
    echo "Schema initialized successfully."
else
    echo "Existing Derby schema found — skipping init."
fi

# Start the Thrift metastore server
echo "Starting Thrift metastore on port ${METASTORE_PORT:-9083}..."
exec ${METASTORE_HOME}/bin/start-metastore