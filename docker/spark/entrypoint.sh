#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Spark Container Entrypoint
# Supports: master | worker | history-server
# Usage: pass role as first argument to container
# ═══════════════════════════════════════════════════════════════════

set -eo pipefail

SPARK_HOME=${SPARK_HOME:-/opt/spark}

# Ensure event log directory exists
mkdir -p "${SPARK_HOME}/spark-events"

case "$1" in

  master)
    echo "Starting Spark Master..."
    echo "  SPARK_HOME   : ${SPARK_HOME}"
    echo "  SPARK_MASTER : spark://${SPARK_MASTER_HOST}:7077"
    exec "${SPARK_HOME}/bin/spark-class" \
      org.apache.spark.deploy.master.Master \
      --host "${SPARK_MASTER_HOST:-spark-master}" \
      --port 7077 \
      --webui-port 8080
    ;;

  worker)
    echo "Starting Spark Worker..."
    echo "  SPARK_HOME       : ${SPARK_HOME}"
    echo "  SPARK_MASTER_URL : ${SPARK_MASTER_URL}"
    echo "  SPARK_WORKER_CORES  : ${SPARK_WORKER_CORES:-1}"
    echo "  SPARK_WORKER_MEMORY : ${SPARK_WORKER_MEMORY:-1g}"
    exec "${SPARK_HOME}/bin/spark-class" \
      org.apache.spark.deploy.worker.Worker \
      --cores "${SPARK_WORKER_CORES:-1}" \
      --memory "${SPARK_WORKER_MEMORY:-1g}" \
      --webui-port "${SPARK_WORKER_WEBUI_PORT:-8081}" \
      "${SPARK_MASTER_URL:-spark://spark-master:7077}"
    ;;

  history-server)
    echo "Starting Spark History Server..."
    echo "  SPARK_HOME        : ${SPARK_HOME}"
    echo "  SPARK_EVENTS_DIR  : ${SPARK_EVENTS_DIR}"
    export SPARK_HISTORY_OPTS="-Dspark.history.fs.logDirectory=${SPARK_EVENTS_DIR:-/opt/spark/spark-events}"
    exec "${SPARK_HOME}/bin/spark-class" \
      org.apache.spark.deploy.history.HistoryServer
    ;;

  *)
    echo "Usage: entrypoint.sh [master|worker|history-server]"
    echo "Unknown role: $1"
    exit 1
    ;;

esac
