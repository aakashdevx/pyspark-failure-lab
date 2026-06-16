"""
Phase 3 Smoke Test
End-to-end integration test: Spark -> Hive Metastore -> MinIO
Run with: python scripts/smoke_test_phase3.py
"""
import subprocess
import sys

PYSPARK_SCRIPT = """
from pyspark.sql import SparkSession
import sys

spark = SparkSession.builder.appName('phase3-smoke-test').getOrCreate()

try:
    print('PASS | SparkSession created with Hive support')

    spark.sql('CREATE DATABASE IF NOT EXISTS phase3_smoke')
    print('PASS | Database created in Hive Metastore')

    df = spark.createDataFrame([(1, 'a'), (2, 'b'), (3, 'c')], ['id', 'val'])
    df.write.mode('overwrite').saveAsTable('phase3_smoke.smoke_table')
    print('PASS | Table written to S3A/MinIO via Hive Metastore')

    result = spark.sql('SELECT COUNT(*) as cnt FROM phase3_smoke.smoke_table').collect()[0]['cnt']
    assert result == 3, f"Expected 3 rows, got {result}"
    print(f'PASS | Table read back, row count = {result}')

    spark.sql('DROP TABLE phase3_smoke.smoke_table')
    spark.sql('DROP DATABASE phase3_smoke')
    print('PASS | Cleanup completed')

    print('SMOKE_TEST_RESULT: PASSED')
    spark.stop()
    sys.exit(0)

except Exception as e:
    print(f'FAIL | {type(e).__name__}: {e}')
    print('SMOKE_TEST_RESULT: FAILED')
    spark.stop()
    sys.exit(1)
"""

print("\n=== Phase 3 Smoke Test ===\n")

# Write the test script into the spark-master container
write_result = subprocess.run(
    ["docker", "exec", "-i", "spark-master", "sh", "-c",
     "cat > /tmp/phase3_smoke_test.py"],
    input=PYSPARK_SCRIPT, text=True, capture_output=True
)
if write_result.returncode != 0:
    print(f"  FAIL | Could not write test script into container: {write_result.stderr}")
    sys.exit(1)

# Run it via spark-submit
run_result = subprocess.run(
    ["docker", "exec", "spark-master", "/opt/spark/bin/spark-submit",
     "--master", "spark://spark-master:7077",
     "--conf", "spark.driver.memory=512m",
     "--conf", "spark.executor.memory=512m",
     "/tmp/phase3_smoke_test.py"],
    capture_output=True, text=True, timeout=120
)

output = run_result.stdout + run_result.stderr
for line in output.splitlines():
    if line.startswith("PASS") or line.startswith("FAIL") or "SMOKE_TEST_RESULT" in line:
        print(" ", line)

# Cleanup the script file regardless of outcome
subprocess.run(
    ["docker", "exec", "spark-master", "rm", "-f", "/tmp/phase3_smoke_test.py"],
    capture_output=True, text=True
)

if "SMOKE_TEST_RESULT: PASSED" in output:
    print("\n=== Smoke Test PASSED ===")
    print("Spark <-> Hive Metastore <-> MinIO integration confirmed working.")
    sys.exit(0)
else:
    print("\n=== Smoke Test FAILED ===")
    print("Full output:")
    print(output[-2000:])
    sys.exit(1)