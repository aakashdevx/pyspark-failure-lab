# ═══════════════════════════════════════════════════════════════════
# PySpark Failure Lab — Custom Spark Image
# Base: Eclipse Temurin JRE 17 (ARM64 native)
# Spark: 3.5.3 · Python: 3.11 (matches driver conda env)
# ═══════════════════════════════════════════════════════════════════

FROM eclipse-temurin:17-jre-jammy

LABEL maintainer="pyspark-failure-lab"
LABEL spark.version="3.5.3"
LABEL java.version="17"

ENV SPARK_VERSION=3.5.3
ENV SPARK_HOME=/opt/spark
ENV SPARK_CONF_DIR=/opt/spark/conf
ENV SPARK_LOG_DIR=/opt/spark/logs
ENV SPARK_EVENTS_DIR=/opt/spark/spark-events
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# ── Critical: pin Python 3.11 on both driver and worker ──────────
# PYSPARK_PYTHON  — used by executors inside Docker
# PYSPARK_DRIVER_PYTHON — used by driver (overridden by local conda)
ENV PYSPARK_PYTHON=python3.11
ENV PYSPARK_DRIVER_PYTHON=python3.11

# ── Install Python 3.11 explicitly ───────────────────────────────
# Ubuntu Jammy (22.04) ships Python 3.10 by default
# We add deadsnakes PPA to get Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-distutils \
    python3-pip \
    curl \
    procps \
    tini \
    && rm -rf /var/lib/apt/lists/*

# ── Verify Python 3.11 is available ──────────────────────────────
RUN python3.11 --version

# ── Download and install Spark ────────────────────────────────────
RUN curl -fsSL \
    "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" \
    -o /tmp/spark.tgz \
    && tar -xzf /tmp/spark.tgz -C /opt \
    && mv /opt/spark-${SPARK_VERSION}-bin-hadoop3 ${SPARK_HOME} \
    && rm /tmp/spark.tgz

# ── Create required directories ───────────────────────────────────
RUN mkdir -p \
    ${SPARK_CONF_DIR} \
    ${SPARK_LOG_DIR} \
    ${SPARK_EVENTS_DIR} \
    /opt/spark/work-dir

# ── Create non-root spark user ────────────────────────────────────
RUN groupadd --gid 1000 spark \
    && useradd --uid 1000 --gid spark \
       --shell /bin/bash \
       --home-dir ${SPARK_HOME} spark \
    && chown -R spark:spark ${SPARK_HOME}

# ── Copy configuration files ──────────────────────────────────────
COPY conf/spark-defaults.conf ${SPARK_CONF_DIR}/spark-defaults.conf
COPY conf/log4j2.properties   ${SPARK_CONF_DIR}/log4j2.properties

# ── Copy startup entrypoint ───────────────────────────────────────
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh \
    && chown spark:spark /opt/entrypoint.sh

USER spark
WORKDIR ${SPARK_HOME}

ENTRYPOINT ["/usr/bin/tini", "-s", "--", "/opt/entrypoint.sh"]
