-- ============================================================
-- PaymentPulse SQL Risk Analysis
-- Purpose: Analyze payment approvals, failures, fraud, chargebacks,
-- merchant risk, and operational performance.
-- ============================================================


-- 1. Executive Payment KPIs
-- Business Question:
-- What is the overall health of the payment system?
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


-- 2. Daily Payment Trend
-- Business Question:
-- How do payment volume, approvals, failures, fraud, and chargebacks trend over time?
SELECT
    transaction_date,
    total_transactions,
    total_payment_volume,
    approval_rate_pct,
    failure_rate_pct,
    fraud_rate_pct,
    chargeback_rate_pct
FROM daily_payment_kpis
ORDER BY transaction_date;


-- 3. Top Failure Reasons
-- Business Question:
-- What are the most common reasons transactions fail?
SELECT
    failure_reason,
    transaction_count,
    pct_of_failed_transactions
FROM failure_reason_summary
ORDER BY transaction_count DESC;


-- 4. High-Risk Merchants
-- Business Question:
-- Which merchants show high fraud, chargeback, or failure behavior?
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


-- 5. Fraud by Payment Channel
-- Business Question:
-- Which payment channels have higher fraud rates?
SELECT
    channel,
    COUNT(*) AS total_transactions,
    SUM(is_fraud) AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
    ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount
FROM payment_transactions
GROUP BY channel
ORDER BY fraud_rate_pct DESC;


-- 6. Chargeback by Merchant Category
-- Business Question:
-- Which merchant categories create the highest chargeback exposure?
SELECT
    merchant_category,
    COUNT(*) AS total_transactions,
    SUM(is_chargeback) AS chargebacks,
    ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct,
    ROUND(SUM(transaction_amount), 2) AS total_payment_volume
FROM payment_transactions
GROUP BY merchant_category
ORDER BY chargeback_rate_pct DESC;


-- 7. Weekend vs Weekday Risk
-- Business Question:
-- Are weekend transactions riskier than weekday transactions?
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


-- 8. Processor Response Time Impact
-- Business Question:
-- Are slow processor responses associated with more failures or fraud?
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


-- 9. High-Value Transaction Risk
-- Business Question:
-- Are high-value transactions riskier than standard transactions?
SELECT
    CASE
        WHEN high_value_txn = 1 THEN 'High Value'
        ELSE 'Standard Value'
    END AS transaction_value_type,
    COUNT(*) AS total_transactions,
    ROUND(AVG(transaction_amount), 2) AS avg_transaction_amount,
    ROUND(100.0 * SUM(CASE WHEN transaction_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct,
    ROUND(100.0 * SUM(is_chargeback) / COUNT(*), 2) AS chargeback_rate_pct
FROM payment_transactions
GROUP BY high_value_txn
ORDER BY fraud_rate_pct DESC;


-- 10. Payment Method Performance
-- Business Question:
-- Which payment methods have the highest failure and fraud rates?
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


-- 11. Monthly Risk Trend
-- Business Question:
-- How does payment risk change month by month?
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


-- 12. Location-Based Risk
-- Business Question:
-- Which customer locations have higher payment risk?
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