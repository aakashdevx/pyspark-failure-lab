"""
Phase 4 Validation Script
Run with: python scripts/validate_phase4.py
Validates Delta Lake integration and Phase 4 sample datasets.
"""
import subprocess
import sys
import os

PASS = "  PASS"
FAIL = "  FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"{status} | {label}" + (f" | {detail}" if detail else ""))

def container_status(name):
    result = subprocess.run(
        ["docker", "inspect", "--format",
         "{{.State.Status}}|{{.State.Health.Status}}", name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None, None
    parts = result.stdout.strip().split("|")
    return parts[0], parts[1] if len(parts) > 1 else "none"

print("\n=== Phase 4 Validation ===\n")

# Check 1: All 6 containers still healthy (regression check from Phase 3)
all_services = [
    "spark-master", "spark-worker-1", "spark-worker-2",
    "spark-history", "minio", "hive-metastore"
]
for name in all_services:
    state, health = container_status(name)
    check(f"Container healthy : {name}", health == "healthy", f"health={health}")

# Check 2: Spark image has Delta JARs
result = subprocess.run(
    ["docker", "exec", "spark-master", "sh", "-c",
     "ls /opt/spark/jars/ | grep -i delta"],
    capture_output=True, text=True
)
check("Spark image has delta-spark JAR", "delta-spark" in result.stdout)
check("Spark image has delta-storage JAR", "delta-storage" in result.stdout)

# Check 3: spark-defaults.conf has Delta catalog enabled (uncommented)
result = subprocess.run(
    ["docker", "exec", "spark-master", "cat", "/opt/spark/conf/spark-defaults.conf"],
    capture_output=True, text=True
)
conf_lines = result.stdout.splitlines()
delta_ext_active = any(
    line.strip().startswith("spark.sql.extensions") and "DeltaSparkSessionExtension" in line
    for line in conf_lines
)
delta_catalog_active = any(
    line.strip().startswith("spark.sql.catalog.spark_catalog") and "DeltaCatalog" in line
    for line in conf_lines
)
check("spark.sql.extensions DeltaSparkSessionExtension active", delta_ext_active)
check("spark.sql.catalog.spark_catalog DeltaCatalog active", delta_catalog_active)

# Check 4: MinIO datasets exist
result = subprocess.run(
    ["docker", "run", "--rm", "--network", "spark-lab-net", "--entrypoint", "sh",
     "minio/mc:latest", "-c",
     "mc alias set local http://minio:9000 minioadmin minioadmin123 >/dev/null 2>&1 && "
     "mc ls local/spark-warehouse/datasets/ && echo '---DELTA_LOG---' && "
     "mc ls local/delta-tables/orders_evolved/_delta_log/"],
    capture_output=True, text=True, timeout=30
)
mc_output = result.stdout
check("Dataset exists: transactions_skewed", "transactions_skewed" in mc_output)
check("Dataset exists: transactions_clean", "transactions_clean" in mc_output)
json_count = mc_output.split("---DELTA_LOG---")[-1].count(".json")
check("Delta table _delta_log has exactly 2 commits",
      json_count == 2, f"found {json_count} json files")

# Check 5: Local malformed files exist
data_input = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "input"
)
for fname in ["malformed_transactions.csv", "malformed_events.json",
              "corrupt_data.parquet", "schema_drift_transactions.csv"]:
    check(f"Local file exists: {fname}", os.path.isfile(os.path.join(data_input, fname)))

# Check 6: data/ mounted into all job-running Spark containers
for name in ["spark-master", "spark-worker-1", "spark-worker-2"]:
    result = subprocess.run(
        ["docker", "exec", name, "test", "-f", "/data/input/malformed_transactions.csv"],
        capture_output=True, text=True
    )
    check(f"data/ mounted in {name}", result.returncode == 0)

print("\n=== Summary ===")
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total = len(results)
print(f"Passed : {passed}/{total}")
print(f"Failed : {failed}/{total}")
if failed == 0:
    print("\nPhase 4 infrastructure: COMPLETE.")
else:
    print("\nPhase 4 INCOMPLETE. Fix FAIL items above.")
    sys.exit(1)