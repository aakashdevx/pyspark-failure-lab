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

# ── Add S3A connectivity JARs ──────────────────────────────────
# Spark's hadoop3 binary distribution does NOT bundle hadoop-aws
# or the AWS SDK. Required for s3a:// (MinIO) connectivity.
# Version 3.3.4 matches hadoop-client-api/runtime already bundled
# in Spark 3.5.3 — confirmed via: ls /opt/spark/jars | grep hadoop-client
ENV HADOOP_AWS_VERSION=3.3.4
ENV AWS_SDK_BUNDLE_VERSION=1.12.367
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
    -o ${SPARK_HOME}/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar \
    && curl -fsSL \
    "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_BUNDLE_VERSION}/aws-java-sdk-bundle-${AWS_SDK_BUNDLE_VERSION}.jar" \
    -o ${SPARK_HOME}/jars/aws-java-sdk-bundle-${AWS_SDK_BUNDLE_VERSION}.jar

# ── Add Delta Lake JARs ─────────────────────────────────────────
# delta-spark: core Delta Lake library
# delta-storage: storage abstraction layer Delta depends on
# Scala 2.12 suffix matches Spark 3.5.3's Scala build version
# (confirmed via spark-examples_2.12-3.5.3.jar filename)
ENV DELTA_VERSION=3.2.1
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/${DELTA_VERSION}/delta-spark_2.12-${DELTA_VERSION}.jar" \
    -o ${SPARK_HOME}/jars/delta-spark_2.12-${DELTA_VERSION}.jar \
    && curl -fsSL \
    "https://repo1.maven.org/maven2/io/delta/delta-storage/${DELTA_VERSION}/delta-storage-${DELTA_VERSION}.jar" \
    -o ${SPARK_HOME}/jars/delta-storage-${DELTA_VERSION}.jar

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
