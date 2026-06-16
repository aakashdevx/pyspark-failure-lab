"""
Phase 3 Validation Script
Run with: python scripts/validate_phase3.py
Validates that MinIO + Hive Metastore are healthy and integrated
with the existing Spark cluster from Phase 2.
"""
import subprocess
import sys
import urllib.request

PASS = "  PASS"
FAIL = "  FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"{status} | {label}" + (f" | {detail}" if detail else ""))

def http_check(url, timeout=5):
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return req.status in (200, 403)  # MinIO root returns 403, that's fine
    except Exception:
        return False

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

def port_open(container, host, port):
    result = subprocess.run(
        ["docker", "exec", container, "nc", "-zv", host, str(port)],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0

print("\n=== Phase 3 Validation ===\n")

# Check 1: All 6 containers running + healthy
all_services = [
    "spark-master", "spark-worker-1", "spark-worker-2",
    "spark-history", "minio", "hive-metastore"
]
for name in all_services:
    state, health = container_status(name)
    check(f"Container running : {name}", state == "running", f"state={state}")
    check(f"Container healthy : {name}", health == "healthy", f"health={health}")

# Check 2: MinIO Web UIs reachable
check("Reachable: MinIO API (9000)", http_check("http://localhost:9000/minio/health/live"))
check("Reachable: MinIO Console (9001)", http_check("http://localhost:9001"))

# Check 3: Hive Metastore Thrift port open (via nc, more reliable than /proc/net/tcp)
check("Hive Metastore port 9083 open",
      port_open("hive-metastore", "localhost", 9083))

# Check 4: MinIO buckets exist
result = subprocess.run(
    ["docker", "run", "--rm", "--network", "spark-lab-net", "--entrypoint", "sh",
     "minio/mc:latest", "-c",
     "mc alias set local http://minio:9000 minioadmin minioadmin123 >/dev/null 2>&1 && mc ls local"],
    capture_output=True, text=True, timeout=30
)
buckets_output = result.stdout
for bucket in ["spark-warehouse", "spark-logs", "delta-tables"]:
    check(f"MinIO bucket exists: {bucket}", bucket in buckets_output)

# Check 5: Spark image has S3A JARs
result = subprocess.run(
    ["docker", "exec", "spark-master", "sh", "-c",
     "ls /opt/spark/jars/ | grep -i -E 'hadoop-aws|aws-java-sdk'"],
    capture_output=True, text=True
)
check("Spark image has hadoop-aws JAR", "hadoop-aws" in result.stdout)
check("Spark image has aws-java-sdk-bundle JAR", "aws-java-sdk" in result.stdout)

# Check 6: spark-defaults.conf has required settings (checked inside container)
result = subprocess.run(
    ["docker", "exec", "spark-master", "cat", "/opt/spark/conf/spark-defaults.conf"],
    capture_output=True, text=True
)
conf_content = result.stdout
for setting in ["fs.s3a.endpoint", "hive.metastore.uris", "catalogImplementation"]:
    check(f"spark-defaults.conf has: {setting}", setting in conf_content)

# Summary
print("\n=== Summary ===")
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total = len(results)
print(f"Passed : {passed}/{total}")
print(f"Failed : {failed}/{total}")
if failed == 0:
    print("\nPhase 3 infrastructure: COMPLETE.")
    print("Proceed to integration test: python scripts/smoke_test_phase3.py")
else:
    print("\nPhase 3 INCOMPLETE. Fix FAIL items above.")
    sys.exit(1)