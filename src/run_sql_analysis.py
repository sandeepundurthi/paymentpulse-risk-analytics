import os
import sqlite3
import pandas as pd

DB_PATH = "data/paymentpulse.db"
OUTPUT_DIR = "reports/sql_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

queries = {
    "executive_payment_kpis": """
        SELECT
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
        FROM payment_transactions;
    """,

    "top_failure_reasons": """
        SELECT
            failure_reason,
            transaction_count,
            pct_of_failed_transactions
        FROM failure_reason_summary
        ORDER BY transaction_count DESC;
    """,

    "high_risk_merchants": """
        SELECT
            merchant_id,
            merchant_category,
            total_transactions,
            total_payment_volume,
            avg_transaction_amount,
            failure_rate_pct,
            fraud_rate_pct,
            chargeback_rate_pct,
            merchant_risk_level
        FROM merchant_risk_summary
        WHERE merchant_risk_level = 'High Risk'
        ORDER BY fraud_rate_pct DESC, chargeback_rate_pct DESC
        LIMIT 25;
    """,

    "fraud_by_channel": """
        SELECT
            channel,
            COUNT(*) AS total_transactions,
            SUM(is_fraud) AS fraud_transactions,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount
        FROM payment_transactions
        GROUP BY channel
        ORDER BY fraud_rate_pct DESC;
    """,

    "chargeback_by_category": """
        SELECT
            merchant_category,
            COUNT(*) AS total_transactions,
            SUM(is_chargeback) AS chargebacks,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct,
            ROUND(SUM(transaction_amount), 2) AS total_payment_volume
        FROM payment_transactions
        GROUP BY merchant_category
        ORDER BY chargeback_rate_pct DESC;
    """,

    "weekend_vs_weekday_risk": """
        SELECT
            CASE
                WHEN is_weekend = 1 THEN 'Weekend'
                ELSE 'Weekday'
            END AS day_type,
            COUNT(*) AS total_transactions,
            ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount,
            ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
        FROM payment_transactions
        GROUP BY is_weekend
        ORDER BY fraud_rate_pct DESC;
    """,

    "slow_response_impact": """
        SELECT
            CASE
                WHEN slow_response = 1 THEN 'Slow Response'
                ELSE 'Normal Response'
            END AS response_type,
            COUNT(*) AS total_transactions,
            ROUND(AVG(processor_response_ms), 2) AS avg_processor_response_ms,
            ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
        FROM payment_transactions
        GROUP BY slow_response
        ORDER BY failure_rate_pct DESC;
    """,

    "payment_method_performance": """
        SELECT
            payment_method,
            COUNT(*) AS total_transactions,
            ROUND(SUM(transaction_amount), 2) AS total_payment_volume,
            ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount,
            ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
        FROM payment_transactions
        GROUP BY payment_method
        ORDER BY failure_rate_pct DESC;
    """,

    "monthly_risk_trend": """
        SELECT
            month,
            COUNT(*) AS total_transactions,
            ROUND(SUM(transaction_amount), 2) AS total_payment_volume,
            ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
        FROM payment_transactions
        GROUP BY month
        ORDER BY month;
    """,

    "location_based_risk": """
        SELECT
            customer_location,
            COUNT(*) AS total_transactions,
            ROUND(SUM(transaction_amount), 2) AS total_payment_volume,
            ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
            ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
            ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
        FROM payment_transactions
        GROUP BY customer_location
        HAVING COUNT(*) >= 100
        ORDER BY fraud_rate_pct DESC;
    """
}

conn = sqlite3.connect(DB_PATH)

print("Running PaymentPulse SQL analysis...")
print("------------------------------------")

for name, query in queries.items():
    df = pd.read_sql_query(query, conn)
    output_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(output_path, index=False)

    print(f"\n{name}")
    print("-" * len(name))
    print(df.head())
    print(f"Saved to: {output_path}")

conn.close()

print("\nStep 4 SQL analysis complete.")
print(f"All outputs saved to: {OUTPUT_DIR}")
