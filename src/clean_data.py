import os
import pandas as pd
import numpy as np

# ---------------------------
# Paths
# ---------------------------
RAW_FILE = "data/raw/payment_transactions.csv"
OUT_DIR = "data/processed"
OUT_FILE = f"{OUT_DIR}/clean_payment_transactions.csv"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------
# Load raw data
# ---------------------------
df = pd.read_csv(RAW_FILE)

print("Loaded raw dataset")
print("-------------------")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

# ---------------------------
# Remove duplicates
# ---------------------------
before = df.shape[0]
df = df.drop_duplicates()
after = df.shape[0]

duplicates_removed = before - after

# ---------------------------
# Convert datetime
# ---------------------------
df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])

# ---------------------------
# Handle missing values
# ---------------------------

# Fill location with Unknown
df["customer_location"] = df["customer_location"].fillna("Unknown")

# Fill merchant category with Other
df["merchant_category"] = df["merchant_category"].fillna("Other")

# ---------------------------
# Validate transaction amounts
# ---------------------------
invalid_amounts = (df["transaction_amount"] <= 0).sum()

# remove invalid amounts if any
df = df[df["transaction_amount"] > 0]

# ---------------------------
# Validate statuses
# ---------------------------
valid_status = ["Approved", "Failed"]
invalid_status = (~df["transaction_status"].isin(valid_status)).sum()

df = df[df["transaction_status"].isin(valid_status)]

# ---------------------------
# Create Time Features
# ---------------------------
df["transaction_date"] = df["transaction_datetime"].dt.date
df["hour"] = df["transaction_datetime"].dt.hour
df["day_of_week"] = df["transaction_datetime"].dt.day_name()
df["month"] = df["transaction_datetime"].dt.month
df["year"] = df["transaction_datetime"].dt.year
df["is_weekend"] = df["day_of_week"].isin(
    ["Saturday", "Sunday"]
).astype(int)

# ---------------------------
# Additional Derived Features
# ---------------------------
df["is_failed"] = (df["transaction_status"] == "Failed").astype(int)

# High value flag
df["high_value_txn"] = (df["transaction_amount"] >= 500).astype(int)

# Slow processor flag
df["slow_response"] = (df["processor_response_ms"] >= 900).astype(int)

# ---------------------------
# Save clean data
# ---------------------------
df.to_csv(OUT_FILE, index=False)

# ---------------------------
# Reporting
# ---------------------------
print("\nCleaning Completed")
print("-------------------")
print("Duplicates removed:", duplicates_removed)
print("Invalid amounts removed:", invalid_amounts)
print("Invalid statuses removed:", invalid_status)

print("\nFinal Dataset Shape:")
print(df.shape)

print("\nMissing Values Remaining:")
print(df.isnull().sum())

print("\nApproval Rate:")
print(round((df["transaction_status"].eq("Approved").mean()) * 100, 2), "%")

print("\nFraud Rate:")
print(round(df["is_fraud"].mean() * 100, 2), "%")

print("\nChargeback Rate:")
print(round(df["is_chargeback"].mean() * 100, 2), "%")

print("\nSaved cleaned file:")
print(OUT_FILE)
