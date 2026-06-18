"""
Phase 4 Dataset Seeder
Generates sample datasets directly into MinIO for use in later
failure scenario phases (skew, schema evolution, Delta).

This script is intended to run INSIDE the spark-master container
via spark-submit, not on the local host.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, LongType, StringType, DoubleType, IntegerType

spark = SparkSession.builder.appName("phase4-seed-datasets").getOrCreate()

print("=== Seeding Dataset 1: transactions_skewed ===")
print("80% of 100,000 rows share customer_id=1 (extreme skew)")

# 80,000 rows all with customer_id = 1
skewed_part = spark.range(0, 80000).select(
    F.col("id").alias("transaction_id"),
    F.lit(1).cast(LongType()).alias("customer_id"),
    (F.rand() * 500).alias("amount")
)
# 20,000 rows spread across 50 other customer_ids
normal_part = spark.range(0, 20000).select(
    (F.col("id") + 80000).alias("transaction_id"),
    ((F.col("id") % 50) + 2).cast(LongType()).alias("customer_id"),
    (F.rand() * 500).alias("amount")
)
transactions_skewed = skewed_part.union(normal_part)
transactions_skewed.write.mode("overwrite").parquet(
    "s3a://spark-warehouse/datasets/transactions_skewed"
)
print(f"Written: {transactions_skewed.count()} rows")

print("=== Seeding Dataset 2: transactions_clean ===")
print("Same schema, evenly distributed across 100 customer_ids")

transactions_clean = spark.range(0, 100000).select(
    F.col("id").alias("transaction_id"),
    ((F.col("id") % 100) + 1).cast(LongType()).alias("customer_id"),
    (F.rand() * 500).alias("amount")
)
transactions_clean.write.mode("overwrite").parquet(
    "s3a://spark-warehouse/datasets/transactions_clean"
)
print(f"Written: {transactions_clean.count()} rows")

print("=== Seeding Dataset 3: orders_evolved (Delta, schema evolution history) ===")

delta_path = "s3a://delta-tables/orders_evolved"

# Idempotency: delete any prior run's data so version history always
# starts clean at v0, regardless of how many times this script runs.
hadoop_conf = spark._jsc.hadoopConfiguration()
path = spark._jvm.org.apache.hadoop.fs.Path(delta_path)
uri = spark._jvm.java.net.URI(delta_path)
fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(uri, hadoop_conf)
if fs.exists(path):
    fs.delete(path, True)
    print(f"Cleaned up existing path: {delta_path}")

# v0 — base schema
orders_v0 = spark.createDataFrame(
    [(1, 101, 49.99), (2, 102, 19.50), (3, 103, 99.00)],
    ["order_id", "customer_id", "amount"]
)
orders_v0.write.format("delta").mode("overwrite").save(delta_path)
print("Delta v0 written: order_id, customer_id, amount")

# v1 — append a new nullable column via mergeSchema (safe evolution)
orders_v1 = spark.createDataFrame(
    [(4, 104, 150.00, "APAC"), (5, 105, 75.25, "EMEA")],
    ["order_id", "customer_id", "amount", "region"]
)
orders_v1.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save(delta_path)
print("Delta v1 written: added 'region' column via mergeSchema")

print("=== Verification ===")
spark.read.format("delta").load(delta_path).orderBy("order_id").show()
history_query = f"DESCRIBE HISTORY delta.`{delta_path}`"
version_count = spark.sql(history_query).count()
print(f"Delta table version count: {version_count}")

print("=== SEEDING COMPLETE ===")
spark.stop()