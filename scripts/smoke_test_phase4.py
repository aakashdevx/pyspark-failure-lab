"""
Phase 4 Smoke Test
End-to-end test: Delta Lake read/write/time-travel against MinIO,
plus verification of seeded sample datasets and malformed file
handling behavior.
Run with: python scripts/smoke_test_phase4.py
"""
import subprocess
import sys

PYSPARK_SCRIPT = """
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName('phase4-smoke-test').getOrCreate()

try:
    print('PASS | SparkSession created with Delta + Hive support')

    skewed = spark.read.parquet('s3a://spark-warehouse/datasets/transactions_skewed')
    skewed_count = skewed.count()
    assert skewed_count == 100000, f"Expected 100000 rows, got {skewed_count}"
    print(f'PASS | transactions_skewed row count = {skewed_count}')

    top_customer_count = skewed.filter(skewed.customer_id == 1).count()
    skew_ratio = top_customer_count / skewed_count
    assert skew_ratio > 0.7, f"Expected heavy skew, got ratio={skew_ratio}"
    print(f'PASS | transactions_skewed confirmed skewed: customer_id=1 has {skew_ratio:.0%} of rows')

    clean = spark.read.parquet('s3a://spark-warehouse/datasets/transactions_clean')
    clean_count = clean.count()
    assert clean_count == 100000, f"Expected 100000 rows, got {clean_count}"
    print(f'PASS | transactions_clean row count = {clean_count}')

    delta_path = 's3a://delta-tables/orders_evolved'
    history = spark.sql(f"DESCRIBE HISTORY delta.`{delta_path}`")
    version_count = history.count()
    assert version_count == 2, f"Expected 2 versions, got {version_count}"
    print(f'PASS | orders_evolved Delta history has exactly {version_count} versions')

    latest = spark.read.format('delta').load(delta_path)
    assert 'region' in latest.columns, "Expected 'region' column in latest version"
    latest_count = latest.count()
    assert latest_count == 5, f"Expected 5 rows, got {latest_count}"
    print(f'PASS | latest version has region column and {latest_count} rows')

    v0 = spark.read.format('delta').option('versionAsOf', 0).load(delta_path)
    v0_count = v0.count()
    assert v0_count == 3, f"Expected 3 rows at v0, got {v0_count}"
    assert 'region' not in v0.columns, "v0 should NOT have region column"
    print(f'PASS | version 0 (pre-evolution) has {v0_count} rows, no region column')

    import os
    for fname in ['malformed_transactions.csv', 'malformed_events.json',
                  'corrupt_data.parquet', 'schema_drift_transactions.csv']:
        path = f'/data/input/{fname}'
        assert os.path.isfile(path), f"Missing: {path}"
    print('PASS | All 4 malformed sample files accessible at /data/input/')

    corrupt_failed_as_expected = False
    try:
        spark.read.parquet('file:///data/input/corrupt_data.parquet').count()
    except Exception:
        corrupt_failed_as_expected = True

    if corrupt_failed_as_expected:
        print('PASS | corrupt_data.parquet correctly fails to parse (intended for Phase 9)')
    else:
        print('FAIL | corrupt_data.parquet was read without error -- expected a failure')
        raise AssertionError("corrupt parquet did not fail as expected")

    print('SMOKE_TEST_RESULT: PASSED')
    spark.stop()
    sys.exit(0)

except Exception as e:
    print(f'FAIL | {type(e).__name__}: {e}')
    print('SMOKE_TEST_RESULT: FAILED')
    spark.stop()
    sys.exit(1)
"""

print("\n=== Phase 4 Smoke Test ===\n")

write_result = subprocess.run(
    ["docker", "exec", "-i", "spark-master", "sh", "-c",
     "cat > /tmp/phase4_smoke_test.py"],
    input=PYSPARK_SCRIPT, text=True, capture_output=True
)
if write_result.returncode != 0:
    print(f"  FAIL | Could not write test script into container: {write_result.stderr}")
    sys.exit(1)

run_result = subprocess.run(
    ["docker", "exec", "spark-master", "/opt/spark/bin/spark-submit",
     "--master", "spark://spark-master:7077",
     "--conf", "spark.driver.memory=512m",
     "--conf", "spark.executor.memory=512m",
     "/tmp/phase4_smoke_test.py"],
    capture_output=True, text=True, timeout=120
)

output = run_result.stdout + run_result.stderr
for line in output.splitlines():
    if line.startswith("PASS") or line.startswith("FAIL") or "SMOKE_TEST_RESULT" in line:
        print(" ", line)

subprocess.run(
    ["docker", "exec", "spark-master", "rm", "-f", "/tmp/phase4_smoke_test.py"],
    capture_output=True, text=True
)

if "SMOKE_TEST_RESULT: PASSED" in output:
    print("\n=== Smoke Test PASSED ===")
    sys.exit(0)
else:
    print("\n=== Smoke Test FAILED ===")
    sys.exit(1)