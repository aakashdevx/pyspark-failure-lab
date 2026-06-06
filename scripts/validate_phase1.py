"""
Phase 1 Validation Script
Run with: python scripts/validate_phase1.py
All checks must pass before confirming Phase 1 complete.
"""
import sys
import os
import subprocess

PASS = "  PASS"
FAIL = "  FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    print(f"{status} | {label}" + (f" | {detail}" if detail else ""))

print("\n=== Phase 1 Validation ===\n")

# Check 1: Python version
major, minor = sys.version_info.major, sys.version_info.minor
check("Python version is 3.11.x",
      major == 3 and minor == 11,
      f"Found: {sys.version.split()[0]}")

# Check 2: PySpark importable and correct version
try:
    import pyspark
    check("PySpark importable", True, f"version: {pyspark.__version__}")
    check("PySpark version is 3.5.3", pyspark.__version__ == "3.5.3", pyspark.__version__)
except ImportError as e:
    check("PySpark importable", False, str(e))
    check("PySpark version is 3.5.3", False, "not installed")

# Check 3: Delta importable
try:
    import delta
    check("Delta-spark importable", True, f"version: {delta.__version__}")
    check("Delta version is 3.2.1", delta.__version__ == "3.2.1", delta.__version__)
except ImportError as e:
    check("Delta-spark importable", False, str(e))

# Check 4: pytest importable
try:
    import pytest
    check("pytest importable", True, f"version: {pytest.__version__}")
except ImportError as e:
    check("pytest importable", False, str(e))

# Check 5: boto3 importable
try:
    import boto3
    check("boto3 importable", True, f"version: {boto3.__version__}")
except ImportError as e:
    check("boto3 importable", False, str(e))

# Check 6: Project directory structure
base = "/Users/aakashdeep/Documents/projects/spark_failure_project"
required_dirs = [
    "docker", "notebooks", "scenarios/01_memory_gc",
    "scenarios/02_data_skew", "scenarios/03_shuffle",
    "scenarios/04_serialization", "scenarios/05_schema_data",
    "scenarios/06_streaming", "scenarios/07_resource_config",
    "data/input", "data/output", "data/checkpoints",
    "scripts", "tests", "docs",
    "monitoring/prometheus", "monitoring/grafana/dashboards"
]
for d in required_dirs:
    full = os.path.join(base, d)
    check(f"Directory exists: {d}", os.path.isdir(full))

# Check 7: Key files exist
required_files = [".gitignore", "PROJECT_LOG.md", ".vscode/settings.json"]
for f in required_files:
    full = os.path.join(base, f)
    check(f"File exists: {f}", os.path.isfile(full))

# Check 8: Docker CLI reachable
try:
    result = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                            capture_output=True, text=True, timeout=10)
    docker_ok = result.returncode == 0 and len(result.stdout.strip()) > 0
    check("Docker daemon reachable", docker_ok,
          f"version: {result.stdout.strip()}" if docker_ok else result.stderr.strip())
except Exception as e:
    check("Docker daemon reachable", False, str(e))

# Check 9: Git repo initialized
git_dir = os.path.join(base, ".git")
check("Git repository initialized", os.path.isdir(git_dir))

# Summary
print("\n=== Summary ===")
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
total = len(results)
print(f"Passed: {passed}/{total}")
print(f"Failed: {failed}/{total}")
if failed == 0:
    print("\nPhase 1 COMPLETE. All checks passed.")
    print("Reply 'Move to next phase' to proceed to Phase 2.")
else:
    print("\nPhase 1 INCOMPLETE. Fix the FAIL items above before confirming.")
    sys.exit(1)
