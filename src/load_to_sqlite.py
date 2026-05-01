import os
import sqlite3
import pandas as pd

# -----------------------------
# Paths
# -----------------------------
CLEAN_FILE = "data/processed/clean_payment_transactions.csv"
DB_PATH = "data/paymentpulse.db"
REPORTS_DIR = "reports"

os.makedirs("data", exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# -----------------------------
# Load clean dataset
# -----------------------------
df = pd.read_csv(CLEAN_FILE)

print("Loaded clean dataset")
print("--------------------")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

# Convert datetime columns to string format for SQLite compatibility
df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"]).astype(str)
df["transaction_date"] = pd.to_datetime(df["transaction_date"]).astype(str)

# Fix failure_reason nulls for reporting clarity
df["failure_reason"] = df["failure_reason"].fillna("Not Applicable")

# -----------------------------
# Create SQLite connection
# -----------------------------
conn = sqlite3.connect(DB_PATH)

# -----------------------------
# Load main table
# -----------------------------
df.to_sql(
    "payment_transactions",
    conn,
    if_exists="replace",
    index=False
)

print("\nMain table loaded: payment_transactions")

# -----------------------------
# Create Reporting Table 1:
# Daily Payment KPIs
# -----------------------------
daily_payment_kpis_query = """
DROP TABLE IF EXISTS daily_payment_kpis;

CREATE TABLE daily_payment_kpis AS
SELECT
    transaction_date,
    COUNT(*) AS total_transactions,
    ROUND(SUM(transaction_amount), 2) AS total_payment_volume,
    SUM(CASE WHEN transaction_status = 'Approved' THEN 1 ELSE 0 END) AS approved_transactions,
    SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transactions,
    SUM(is_fraud) AS fraud_transactions,
    SUM(is_chargeback) AS chargeback_transactions,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Approved' THEN 1 ELSE 0 END) / COUNT(*), 2) AS approval_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
    ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
FROM payment_transactions
GROUP BY transaction_date
ORDER BY transaction_date;
"""

conn.executescript(daily_payment_kpis_query)
print("Reporting table created: daily_payment_kpis")

# -----------------------------
# Create Reporting Table 2:
# Merchant Risk Summary
# -----------------------------
merchant_risk_summary_query = """
DROP TABLE IF EXISTS merchant_risk_summary;

CREATE TABLE merchant_risk_summary AS
SELECT
    merchant_id,
    merchant_category,
    COUNT(*) AS total_transactions,
    ROUND(SUM(transaction_amount), 2) AS total_payment_volume,
    ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount,
    SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transactions,
    SUM(is_fraud) AS fraud_transactions,
    SUM(is_chargeback) AS chargeback_transactions,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
    ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct,
    CASE
        WHEN ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) >= 8
          OR ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) >= 4
          OR ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) >= 15
        THEN 'High Risk'
        WHEN ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) >= 5
          OR ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) >= 2.5
          OR ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) >= 10
        THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS merchant_risk_level
FROM payment_transactions
GROUP BY merchant_id, merchant_category
HAVING COUNT(*) >= 20
ORDER BY fraud_rate_pct DESC, chargeback_rate_pct DESC;
"""

conn.executescript(merchant_risk_summary_query)
print("Reporting table created: merchant_risk_summary")

# -----------------------------
# Create Reporting Table 3:
# Failure Reason Summary
# -----------------------------
failure_reason_summary_query = """
DROP TABLE IF EXISTS failure_reason_summary;

CREATE TABLE failure_reason_summary AS
SELECT
    failure_reason,
    COUNT(*) AS transaction_count,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*)
        FROM payment_transactions
        WHERE transaction_status = 'Failed'
    ), 2) AS pct_of_failed_transactions
FROM payment_transactions
WHERE transaction_status = 'Failed'
GROUP BY failure_reason
ORDER BY transaction_count DESC;
"""

conn.executescript(failure_reason_summary_query)
print("Reporting table created: failure_reason_summary")

# -----------------------------
# Create Reporting Table 4:
# Hourly Risk Summary
# -----------------------------
hourly_risk_summary_query = """
DROP TABLE IF EXISTS hourly_risk_summary;

CREATE TABLE hourly_risk_summary AS
SELECT
    hour,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transactions,
    SUM(is_fraud) AS fraud_transactions,
    SUM(is_chargeback) AS chargeback_transactions,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
    ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
FROM payment_transactions
GROUP BY hour
ORDER BY hour;
"""

conn.executescript(hourly_risk_summary_query)
print("Reporting table created: hourly_risk_summary")

# -----------------------------
# Export reporting tables to CSV
# -----------------------------
tables_to_export = [
    "daily_payment_kpis",
    "merchant_risk_summary",
    "failure_reason_summary",
    "hourly_risk_summary"
]

for table in tables_to_export:
    out_path = f"{REPORTS_DIR}/{table}.csv"
    pd.read_sql_query(f"SELECT * FROM {table}", conn).to_csv(out_path, index=False)
    print(f"Exported: {out_path}")

# -----------------------------
# Print quick database validation
# -----------------------------
print("\nDatabase Validation")
print("-------------------")

tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)

print("\nTables created:")
print(tables)

row_counts = {}
for table in tables["name"]:
    count = pd.read_sql_query(f"SELECT COUNT(*) AS count FROM {table}", conn)["count"][0]
    row_counts[table] = count

print("\nRow counts:")
for table, count in row_counts.items():
    print(f"{table}: {count}")

print("\nTop 5 Merchant Risk Summary:")
top_merchants = pd.read_sql_query(
    """
    SELECT
        merchant_id,
        merchant_category,
        total_transactions,
        failure_rate_pct,
        fraud_rate_pct,
        chargeback_rate_pct,
        merchant_risk_level
    FROM merchant_risk_summary
    ORDER BY fraud_rate_pct DESC, chargeback_rate_pct DESC
    LIMIT 5;
    """,
    conn
)

print(top_merchants)

conn.close()

print("\nStep 3 completed successfully.")
print(f"SQLite database saved to: {DB_PATH}")
