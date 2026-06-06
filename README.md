# pyspark-failure-lab
Local Docker-based lab to reproduce and study real-world PySpark &amp; Spark production failure scenarios

cat > README.md << 'EOF'
# PySpark Failure Lab

A local Docker-based laboratory to reproduce, study, and fix
real-world Apache Spark and PySpark production failure scenarios.

## Purpose
- Reproduce production failures in a safe, controlled environment
- Understand root causes deeply — not just symptoms
- Build muscle memory for debugging Spark jobs
- Prepare for real-world and scenario-based Data Engineering interviews

## Tech Stack
| Component     | Version  |
|---------------|----------|
| Apache Spark  | 3.5.3    |
| PySpark       | 3.5.3    |
| Delta Lake    | 3.2.1    |
| Python        | 3.11.9   |
| Java          | 17.0.18  |
| Docker        | Compose v2 |

## Failure Scenarios Covered
- Memory & GC failures (OOM, GC thrash, off-heap overflow)
- Data skew failures (key skew, partition skew, AQE)
- Shuffle failures (FetchFailedException, disk spill storm)
- Serialization failures (Kryo, UDF closure, non-serializable)
- Schema & data quality failures (corrupt Parquet, Delta evolution)
- Structured Streaming failures (watermark, checkpoint, Kafka)
- Resource & config failures (executor sizing, dynamic allocation)

## Project Status
🚧 Under active construction — building phase by phase.

## Setup
> Detailed setup instructions added per phase.
> See PROJECT_LOG.md for current phase status.

## Requirements
- macOS (Apple Silicon M-series recommended)
- Docker Desktop 4.x+
- Python 3.11 (via conda)
- Java 17
- 16 GB RAM recommended (8 GB minimum)

## Author
Learning project — built phase by phase as a structured
Data Engineering study curriculum.
EOF
