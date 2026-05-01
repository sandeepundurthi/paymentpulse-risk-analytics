import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# -----------------------------
# Configuration
# -----------------------------
RANDOM_SEED = 42
NUM_TRANSACTIONS = 100_000
NUM_CUSTOMERS = 12_000
NUM_MERCHANTS = 800

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


# -----------------------------
# Output path
# -----------------------------
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(RAW_DIR, "payment_transactions.csv")


# -----------------------------
# Reference values
# -----------------------------
payment_methods = ["Credit Card", "Debit Card", "ACH", "Digital Wallet"]
channels = ["Online", "In-Store", "Mobile App"]
device_types = ["Desktop", "Mobile", "Tablet", "POS Terminal"]
merchant_categories = [
    "Retail",
    "Grocery",
    "Fuel",
    "Travel",
    "Restaurant",
    "Electronics",
    "Healthcare",
    "Entertainment",
    "Financial Services",
    "Subscription"
]

locations = [
    "CA", "TX", "NY", "FL", "IL", "WA", "OR", "AZ", "GA", "NC",
    "CO", "NV", "OH", "PA", "MA"
]

failure_reasons = [
    "Insufficient Funds",
    "Expired Card",
    "Suspected Fraud",
    "Invalid Account",
    "Processor Timeout",
    "Network Error",
    "Merchant Decline",
    "Card Limit Exceeded"
]


# -----------------------------
# Generate base transaction data
# -----------------------------
transaction_ids = [f"TXN{str(i).zfill(8)}" for i in range(1, NUM_TRANSACTIONS + 1)]
customer_ids = [f"CUST{random.randint(1, NUM_CUSTOMERS):06d}" for _ in range(NUM_TRANSACTIONS)]
merchant_ids = [f"MERCH{random.randint(1, NUM_MERCHANTS):05d}" for _ in range(NUM_TRANSACTIONS)]

start_date = datetime(2024, 1, 1)
transaction_dates = [
    start_date + timedelta(
        days=random.randint(0, 364),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    for _ in range(NUM_TRANSACTIONS)
]

payment_method_values = np.random.choice(
    payment_methods,
    size=NUM_TRANSACTIONS,
    p=[0.42, 0.31, 0.12, 0.15]
)

channel_values = np.random.choice(
    channels,
    size=NUM_TRANSACTIONS,
    p=[0.45, 0.35, 0.20]
)

device_values = np.random.choice(
    device_types,
    size=NUM_TRANSACTIONS,
    p=[0.32, 0.36, 0.12, 0.20]
)

merchant_category_values = np.random.choice(
    merchant_categories,
    size=NUM_TRANSACTIONS,
    p=[0.18, 0.14, 0.10, 0.08, 0.14, 0.08, 0.08, 0.07, 0.06, 0.07]
)

location_values = np.random.choice(locations, size=NUM_TRANSACTIONS)


# -----------------------------
# Amount distribution
# -----------------------------
# Most payments are small/medium, some are very large.
amounts = np.random.lognormal(mean=3.6, sigma=0.9, size=NUM_TRANSACTIONS)
amounts = np.round(np.clip(amounts, 1.00, 5000.00), 2)


# -----------------------------
# Processor response time
# -----------------------------
processor_response_ms = np.random.normal(loc=450, scale=180, size=NUM_TRANSACTIONS)
processor_response_ms = np.clip(processor_response_ms, 80, 3000).astype(int)


# -----------------------------
# Risk behavior simulation
# -----------------------------
high_risk_categories = ["Travel", "Electronics", "Financial Services"]
high_risk_locations = ["FL", "NV", "NY"]

risk_score_base = np.zeros(NUM_TRANSACTIONS)

risk_score_base += np.where(amounts > 500, 0.20, 0)
risk_score_base += np.where(amounts > 1500, 0.25, 0)
risk_score_base += np.where(np.isin(merchant_category_values, high_risk_categories), 0.15, 0)
risk_score_base += np.where(np.isin(location_values, high_risk_locations), 0.10, 0)
risk_score_base += np.where(channel_values == "Online", 0.08, 0)
risk_score_base += np.where(processor_response_ms > 900, 0.07, 0)

random_noise = np.random.uniform(0, 0.25, size=NUM_TRANSACTIONS)
risk_probability = np.clip(risk_score_base + random_noise, 0, 0.95)


# Fraud probability is intentionally low but risk-dependent.
fraud_probability = 0.015 + (risk_probability * 0.12)
is_fraud = np.random.binomial(1, fraud_probability)


# Failure probability is higher for risky transactions.
failure_probability = 0.04 + (risk_probability * 0.18)
is_failed = np.random.binomial(1, failure_probability)


transaction_status = np.where(is_failed == 1, "Failed", "Approved")


# Failure reasons only apply to failed transactions.
failure_reason_values = []
for failed, fraud in zip(is_failed, is_fraud):
    if failed == 0:
        failure_reason_values.append("None")
    else:
        if fraud == 1:
            failure_reason_values.append(
                np.random.choice(["Suspected Fraud", "Merchant Decline", "Card Limit Exceeded"])
            )
        else:
            failure_reason_values.append(np.random.choice(failure_reasons))


# Chargebacks happen only after approved transactions, more likely if fraud.
chargeback_probability = np.where(is_fraud == 1, 0.18, 0.015)
is_chargeback = np.where(
    transaction_status == "Approved",
    np.random.binomial(1, chargeback_probability),
    0
)


# -----------------------------
# Build DataFrame
# -----------------------------
df = pd.DataFrame({
    "transaction_id": transaction_ids,
    "customer_id": customer_ids,
    "merchant_id": merchant_ids,
    "transaction_datetime": transaction_dates,
    "transaction_amount": amounts,
    "payment_method": payment_method_values,
    "channel": channel_values,
    "device_type": device_values,
    "merchant_category": merchant_category_values,
    "customer_location": location_values,
    "transaction_status": transaction_status,
    "failure_reason": failure_reason_values,
    "processor_response_ms": processor_response_ms,
    "is_fraud": is_fraud,
    "is_chargeback": is_chargeback
})


# -----------------------------
# Add realistic data quality issues
# -----------------------------
# Small number of missing locations
missing_location_idx = np.random.choice(df.index, size=350, replace=False)
df.loc[missing_location_idx, "customer_location"] = np.nan

# Small number of missing merchant categories
missing_category_idx = np.random.choice(df.index, size=250, replace=False)
df.loc[missing_category_idx, "merchant_category"] = np.nan

# Duplicate 100 rows to clean later
duplicate_rows = df.sample(100, random_state=RANDOM_SEED)
df = pd.concat([df, duplicate_rows], ignore_index=True)


# Shuffle rows
df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)


# -----------------------------
# Save
# -----------------------------
df.to_csv(OUTPUT_PATH, index=False)

print("PaymentPulse raw dataset generated successfully.")
print("--------------------------------------------")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")
print(f"Saved to: {OUTPUT_PATH}")

print("\nSample data:")
print(df.head())

print("\nTransaction Status Counts:")
print(df["transaction_status"].value_counts())

print("\nFraud Rate:")
print(round(df["is_fraud"].mean() * 100, 2), "%")

print("\nChargeback Rate:")
print(round(df["is_chargeback"].mean() * 100, 2), "%")
