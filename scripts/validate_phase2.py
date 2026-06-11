"""
Phase 2 Validation Script
Run with: python scripts/validate_phase2.py
"""
import subprocess
import sys
import urllib.request
import json

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
        return req.status == 200
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

print("\n=== Phase 2 Validation ===\n")

# Check 1: Image exists
result = subprocess.run(
    ["docker", "images", "pyspark-failure-lab:3.5.3",
     "--format", "{{.Repository}}:{{.Tag}}"],
    capture_output=True, text=True
)
check("Custom image built: pyspark-failure-lab:3.5.3",
      "pyspark-failure-lab:3.5.3" in result.stdout)

# Check 2: Containers running and healthy
for name in ["spark-master", "spark-worker-1", "spark-worker-2", "spark-history"]:
    state, health = container_status(name)
    check(f"Container running : {name}", state == "running", f"state={state}")
    check(f"Container healthy : {name}", health == "healthy", f"health={health}")

# Check 3: Web UIs reachable
ui_checks = [
    ("Spark Master Web UI",   "http://localhost:8080"),
    ("Spark Worker 1 Web UI", "http://localhost:8081"),
    ("Spark Worker 2 Web UI", "http://localhost:8082"),
    ("History Server Web UI", "http://localhost:18080"),
]
for label, url in ui_checks:
    check(f"Reachable: {label}", http_check(url), url)

# Check 4: Docker network exists
result = subprocess.run(
    ["docker", "network", "inspect", "spark-lab-net"],
    capture_output=True, text=True
)
check("Docker network: spark-lab-net", result.returncode == 0)

# Check 5: Workers registered with master
result = subprocess.run(
    ["docker", "exec", "spark-master",
     "curl", "-s", "http://localhost:8080/json/"],
    capture_output=True, text=True
)
if result.returncode == 0 and result.stdout.strip():
    try:
        data = json.loads(result.stdout)
        alive = data.get("aliveworkers", 0)
        check("Workers registered with master",
              alive == 2, f"alive={alive}/2")
    except Exception as e:
        check("Workers registered with master", False, f"parse error: {e}")
else:
    check("Workers registered with master", False, "could not reach master API")

# Summary
print("\n=== Summary ===")
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total  = len(results)
print(f"Passed : {passed}/{total}")
print(f"Failed : {failed}/{total}")
if failed == 0:
    print("\nPhase 2 cluster health: COMPLETE.")
    print("Proceed to smoke test: python scripts/smoke_test_phase2.py")
else:
    print("\nPhase 2 INCOMPLETE. Fix FAIL items above.")
    sys.exit(1)
