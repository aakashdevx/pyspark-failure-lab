"""
Phase 2 Smoke Test
Submits a real PySpark job to the local Spark cluster.
Run with: python scripts/smoke_test_phase2.py
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import sys
import os

# ── Ensure driver uses Python 3.11 to match workers ──────────────
os.environ["PYSPARK_PYTHON"]        = "python3.11"
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

print("\n=== Phase 2 Smoke Test ===\n")
print(f"  INFO | Driver Python : {sys.executable}")
print(f"  INFO | Driver version: {sys.version.split()[0]}")

try:
    spark = SparkSession.builder \
        .appName("Phase2-SmokeTest") \
        .master("spark://localhost:7077") \
        .config("spark.driver.host", "host.docker.internal") \
        .config("spark.driver.bindAddress", "0.0.0.0") \
        .config("spark.executor.memory", "512m") \
        .config("spark.driver.memory", "512m") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.pyspark.python", "python3.11") \
        .config("spark.pyspark.driver.python", sys.executable) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    print(f"  PASS | SparkSession created")
    print(f"       | Master  : {spark.sparkContext.master}")
    print(f"       | Version : {spark.version}")
    print(f"       | App ID  : {spark.sparkContext.applicationId}")

    # Test 1: Basic RDD
    rdd = spark.sparkContext.parallelize(range(1, 101))
    total = rdd.sum()
    assert total == 5050
    print(f"  PASS | RDD sum(1..100) = {int(total)}")

    # Test 2: DataFrame
    data = [(i, f"user_{i}", float(i * 10)) for i in range(1, 1001)]
    df = spark.createDataFrame(data, ["id", "name", "amount"])
    count = df.count()
    assert count == 1000
    print(f"  PASS | DataFrame rows = {count}")

    # Test 3: Aggregation
    result = df.agg(
        F.count("id").alias("total"),
        F.avg("amount").alias("avg_amount"),
        F.max("amount").alias("max_amount")
    ).collect()[0]
    assert result["total"] == 1000
    print(f"  PASS | Aggregation: total={result['total']}, avg={result['avg_amount']}, max={result['max_amount']}")

    # Test 4: SQL
    df.createOrReplaceTempView("users")
    sql_count = spark.sql(
        "SELECT COUNT(*) as cnt FROM users WHERE amount > 5000"
    ).collect()[0]["cnt"]
    print(f"  PASS | SQL query: {sql_count} rows with amount > 5000")

    print(f"\n=== Smoke Test PASSED ===")
    print(f"Spark UI      : http://localhost:8080")
    print(f"History Server: http://localhost:18080")

    spark.stop()
    sys.exit(0)

except Exception as e:
    print(f"\n  FAIL | {type(e).__name__}: {e}")
    print("\nTroubleshooting:")
    print("  1. docker compose ps        — are all services healthy?")
    print("  2. python scripts/validate_phase2.py")
    print("  3. docker logs spark-master — check master logs")
    sys.exit(1)
