# ================================================================
# PySpark Failure Lab — Custom Hive Metastore Image
# Base: Eclipse Temurin JRE 17 (ARM64 native)
# Hive Metastore: 3.0.0 standalone
# Hadoop AWS JARs: 3.3.6 (for S3A / MinIO connectivity)
# ================================================================

FROM eclipse-temurin:17-jre-jammy

LABEL maintainer="pyspark-failure-lab"
LABEL hive.metastore.version="3.0.0"
LABEL java.version="17"

# ── Environment variables ─────────────────────────────────────
ENV METASTORE_HOME=/opt/hive-metastore
ENV METASTORE_VERSION=3.0.0
ENV HADOOP_VERSION=3.3.6
ENV AWS_SDK_VERSION=1.12.367
ENV METASTORE_PORT=9083
ENV HADOOP_HOME=/opt/hive-metastore/hadoop
ENV HADOOP_COMMON_HOME=/opt/hive-metastore/hadoop
ENV HADOOP_HDFS_HOME=/opt/hive-metastore/hadoop
ENV HADOOP_YARN_HOME=/opt/hive-metastore/hadoop
ENV HADOOP_MAPRED_HOME=/opt/hive-metastore/hadoop
ENV HADOOP_CLASSPATH=/opt/hive-metastore/lib/*
ENV PATH=$PATH:$METASTORE_HOME/bin:$HADOOP_HOME/bin

# ── Install system dependencies ───────────────────────────────
# netcat: used in healthcheck to test port 9083
# curl: download JARs from Maven Central
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ── Download Hive Metastore standalone binary ─────────────────
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/hive/hive-standalone-metastore/${METASTORE_VERSION}/hive-standalone-metastore-${METASTORE_VERSION}-bin.tar.gz" \
    -o /tmp/hive-metastore.tar.gz \
    && tar -xzf /tmp/hive-metastore.tar.gz -C /opt \
    && mv /opt/apache-hive-metastore-${METASTORE_VERSION}-bin ${METASTORE_HOME} \
    && rm /tmp/hive-metastore.tar.gz

# ── Download full Hadoop distribution, extract only what's needed ──
# schematool/start-metastore require a real $HADOOP_HOME/bin/hadoop
# executable plus etc/hadoop config dir. We extract only:
#   - bin/        (hadoop launcher scripts)
#   - libexec/     (hadoop-config.sh, helper scripts)
#   - etc/hadoop/  (default config files, log4j properties)
#   - share/hadoop/common/  (core jars + lib/ dependency jars)
# Everything else (hdfs, mapreduce, yarn, tools, docs, sources)
# is discarded. The tarball itself is deleted after extraction.
RUN curl -fsSL \
    "https://dlcdn.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
    -o /tmp/hadoop.tar.gz \
    && mkdir -p /tmp/hadoop-extract \
    && tar -xzf /tmp/hadoop.tar.gz -C /tmp/hadoop-extract \
        --strip-components=1 \
        "hadoop-${HADOOP_VERSION}/bin" \
        "hadoop-${HADOOP_VERSION}/libexec" \
        "hadoop-${HADOOP_VERSION}/etc/hadoop" \
        "hadoop-${HADOOP_VERSION}/share/hadoop/common" \
        --exclude="hadoop-${HADOOP_VERSION}/share/hadoop/common/sources" \
    && mkdir -p ${METASTORE_HOME}/hadoop/bin \
                ${METASTORE_HOME}/hadoop/libexec \
                ${METASTORE_HOME}/hadoop/etc/hadoop \
                ${METASTORE_HOME}/hadoop/share/hadoop/common \
    && cp -r /tmp/hadoop-extract/bin/.            ${METASTORE_HOME}/hadoop/bin/ \
    && cp -r /tmp/hadoop-extract/libexec/.        ${METASTORE_HOME}/hadoop/libexec/ \
    && cp -r /tmp/hadoop-extract/etc/hadoop/.     ${METASTORE_HOME}/hadoop/etc/hadoop/ \
    && cp -r /tmp/hadoop-extract/share/hadoop/common/.  ${METASTORE_HOME}/hadoop/share/hadoop/common/ \
    && rm -rf /tmp/hadoop.tar.gz /tmp/hadoop-extract

# ── Download Hadoop AWS + AWS SDK JARs for S3A/MinIO connectivity ──
# These are NOT bundled in the trimmed Hadoop above (they live in
# share/hadoop/tools/lib in the full distro, which we excluded).
# We place them directly into the metastore's lib dir so they are
# picked up via CLASSPATH by the base script.
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar" \
    -o ${METASTORE_HOME}/lib/hadoop-aws-${HADOOP_VERSION}.jar \
    && curl -fsSL \
    "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" \
    -o ${METASTORE_HOME}/lib/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar

# ── Create required directories ───────────────────────────────
RUN mkdir -p \
    ${METASTORE_HOME}/conf \
    ${METASTORE_HOME}/data \
    ${METASTORE_HOME}/logs

# ── Create non-root hive user ─────────────────────────────────
RUN groupadd --gid 1001 hive \
    && useradd --uid 1001 --gid hive \
       --shell /bin/bash \
       --home-dir ${METASTORE_HOME} hive \
    && chown -R hive:hive ${METASTORE_HOME}

# ── Copy configuration and entrypoint ────────────────────────
COPY conf/metastore-site.xml ${METASTORE_HOME}/conf/metastore-site.xml
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh \
    && chown hive:hive /opt/entrypoint.sh

USER hive
WORKDIR ${METASTORE_HOME}

EXPOSE 9083

ENTRYPOINT ["/opt/entrypoint.sh"]