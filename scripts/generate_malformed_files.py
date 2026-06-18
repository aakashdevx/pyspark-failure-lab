"""
Phase 4 Malformed File Generator
Generates intentionally broken local files for Phase 9 data quality
failure scenarios. Pure Python, no Spark required.

Run with: python scripts/generate_malformed_files.py
"""
import os
import struct

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "input"
)

def write_malformed_csv():
    path = os.path.join(OUTPUT_DIR, "malformed_transactions.csv")
    lines = [
        "transaction_id,customer_id,amount,currency",
        "1,101,49.99,USD",
        "2,102,19.50",                          # missing column
        "3,103,99.00,EUR,extra_field",           # extra column
        "4,not_a_number,75.25,USD",               # wrong type
        "5,105,,GBP",                              # empty value
        "6,106,150.00,USD",
        "",                                          # blank line
        "7,107,\"unterminated quote,200.00,USD",  # broken quoting
        "8,108,88.88,USD",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Created: {path}")

def write_malformed_json():
    path = os.path.join(OUTPUT_DIR, "malformed_events.json")
    lines = [
        '{"event_id": 1, "user_id": 100, "action": "click"}',
        '{"event_id": 2, "user_id": 101, "action": "view"',     # missing closing brace
        '{"event_id": 3, "user_id": 102, "action": "click"}',
        'not even json at all',                                  # garbage line
        '{"event_id": 5, "user_id": "should_be_int", "action": "purchase"}',
        '',                                                        # blank line
        '{"event_id": 6, "user_id": 105}',                        # missing field
        '{"event_id": 7, "user_id": 106, "action": "click", "extra": {"nested": true}}',
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Created: {path}")

def write_corrupt_parquet():
    """
    Writes a structurally invalid Parquet file by creating a file with
    the correct magic bytes but truncated/corrupted footer metadata.
    This simulates a Parquet file corrupted mid-write (e.g. a crashed
    Spark job that left a partial file behind).
    """
    path = os.path.join(OUTPUT_DIR, "corrupt_data.parquet")
    # Valid Parquet files start and end with the 4-byte magic "PAR1".
    # We write a plausible-looking but truncated/garbled file: magic
    # bytes present, but footer length and metadata are nonsense.
    with open(path, "wb") as f:
        f.write(b"PAR1")                     # magic header
        f.write(os.urandom(200))              # garbage "row group" data
        f.write(struct.pack("<I", 99999))    # bogus footer length (way too large)
        f.write(b"PAR1")                      # magic footer
    print(f"Created: {path}")

def write_schema_drift_csv():
    """
    A 'looks fine at a glance' file that actually has a different
    schema (extra column, renamed column) from a baseline schema,
    for schema-drift detection scenarios.
    """
    path = os.path.join(OUTPUT_DIR, "schema_drift_transactions.csv")
    lines = [
        "txn_id,cust_id,amount,currency,region",   # renamed + extra col
        "1,101,49.99,USD,APAC",
        "2,102,19.50,EUR,EMEA",
        "3,103,99.00,USD,NA",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Created: {path}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}\n")
    write_malformed_csv()
    write_malformed_json()
    write_corrupt_parquet()
    write_schema_drift_csv()
    print("\n=== All malformed files generated ===")