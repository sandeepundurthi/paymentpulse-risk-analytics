import os
import sqlite3
import pandas as pd

DB_PATH = "data/paymentpulse.db"
OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query("SELECT * FROM payment_transactions", conn)

print("Loaded transactions for risk scoring")
print("-----------------------------------")
print("Rows:", df.shape[0])

high_risk_categories = ["Travel", "Electronics", "Financial Services"]
high_risk_locations = ["FL", "NV", "NY"]

scores = []
levels = []
reasons = []

for _, row in df.iterrows():
    score = 0
    reason_list = []

    amount = row["transaction_amount"]

    if amount >= 2000:
        score += 30
        reason_list.append("Very high amount")
    elif amount >= 1000:
        score += 20
        reason_list.append("High amount")
    elif amount >= 500:
        score += 10
        reason_list.append("Elevated amount")

    if row["is_fraud"] == 1:
        score += 40
        reason_list.append("Fraud indicator")

    if row["is_chargeback"] == 1:
        score += 35
        reason_list.append("Chargeback")

    if row["transaction_status"] == "Failed":
        score += 15
        reason_list.append("Failed transaction")

    if row["slow_response"] == 1:
        score += 10
        reason_list.append("Slow processor response")

    if row["channel"] == "Online":
        score += 8
        reason_list.append("Online channel")
    elif row["channel"] == "Mobile App":
        score += 4
        reason_list.append("Mobile channel")

    if row["merchant_category"] in high_risk_categories:
        score += 12
        reason_list.append("High-risk merchant category")

    if row["customer_location"] in high_risk_locations:
        score += 8
        reason_list.append("High-risk location")

    if score >= 75:
        level = "Critical Risk"
    elif score >= 50:
        level = "High Risk"
    elif score >= 25:
        level = "Medium Risk"
    else:
        level = "Low Risk"

    scores.append(score)
    levels.append(level)
    reasons.append(", ".join(reason_list) if reason_list else "No major indicators")

df["risk_score"] = scores
df["risk_level"] = levels
df["risk_reason"] = reasons

df.to_sql("payment_transactions_scored", conn, if_exists="replace", index=False)

summary = pd.read_sql_query(
    """
    SELECT
        risk_level,
        COUNT(*) AS transactions,
        ROUND(AVG(risk_score), 2) AS avg_risk_score,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM payment_transactions_scored), 2) AS pct_total
    FROM payment_transactions_scored
    GROUP BY risk_level
    ORDER BY avg_risk_score DESC;
    """,
    conn
)

top_risk = pd.read_sql_query(
    """
    SELECT
        transaction_id,
        customer_id,
        merchant_id,
        transaction_amount,
        payment_method,
        channel,
        merchant_category,
        customer_location,
        transaction_status,
        is_fraud,
        is_chargeback,
        risk_score,
        risk_level,
        risk_reason
    FROM payment_transactions_scored
    ORDER BY risk_score DESC
    LIMIT 25;
    """,
    conn
)

summary.to_csv(f"{OUTPUT_DIR}/risk_level_summary.csv", index=False)
top_risk.to_csv(f"{OUTPUT_DIR}/top_risk_transactions.csv", index=False)

print("\nRisk Level Summary")
print("------------------")
print(summary)

print("\nTop Risk Transactions")
print("---------------------")
print(top_risk.head(10))

print("\nSaved outputs:")
print("reports/risk_level_summary.csv")
print("reports/top_risk_transactions.csv")
print("SQLite table: payment_transactions_scored")

conn.close()

print("\nStep 5 completed successfully.")
