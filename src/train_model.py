import os
import sqlite3
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


# Optional XGBoost import
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


# -----------------------------
# Paths
# -----------------------------
DB_PATH = "data/paymentpulse.db"
MODEL_DIR = "models"
REPORT_DIR = "reports/model_results"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# -----------------------------
# Load scored transaction data
# -----------------------------
conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    "SELECT * FROM payment_transactions_scored",
    conn
)

conn.close()

print("Loaded scored transactions")
print("--------------------------")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])


# -----------------------------
# Define target
# -----------------------------
target = "is_fraud"

print("\nTarget distribution:")
print(df[target].value_counts(normalize=True).mul(100).round(2))


# -----------------------------
# Select features
# -----------------------------
numeric_features = [
    "transaction_amount",
    "processor_response_ms",
    "hour",
    "month",
    "is_weekend",
    "high_value_txn",
    "slow_response",
    "risk_score"
]

categorical_features = [
    "payment_method",
    "channel",
    "device_type",
    "merchant_category",
    "customer_location",
    "transaction_status"
]

features = numeric_features + categorical_features

X = df[features]
y = df[target]


# -----------------------------
# Train-test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTrain/Test Split")
print("----------------")
print("Train rows:", X_train.shape[0])
print("Test rows:", X_test.shape[0])


# -----------------------------
# Preprocessing
# -----------------------------
numeric_transformer = StandardScaler()

categorical_transformer = OneHotEncoder(
    handle_unknown="ignore"
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)


# -----------------------------
# Model definitions
# -----------------------------
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
}

if XGBOOST_AVAILABLE:
    models["XGBoost"] = XGBClassifier(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42
    )


# -----------------------------
# Train and evaluate
# -----------------------------
results = []

best_model_name = None
best_recall = -1
best_pipeline = None

for model_name, model in models.items():

    print(f"\nTraining model: {model_name}")
    print("-" * (16 + len(model_name)))

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ]
    )

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    if hasattr(pipeline.named_steps["model"], "predict_proba"):
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_proba)
    else:
        y_proba = None
        roc_auc = np.nan

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    cm = confusion_matrix(y_test, y_pred)

    print("Accuracy:", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("F1 Score:", round(f1, 4))
    print("ROC-AUC:", round(roc_auc, 4))
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    results.append({
        "model": model_name,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4)
    })

    # Choose best model by recall first
    if recall > best_recall:
        best_recall = recall
        best_model_name = model_name
        best_pipeline = pipeline


# -----------------------------
# Save model results
# -----------------------------
results_df = pd.DataFrame(results)
results_path = f"{REPORT_DIR}/model_comparison.csv"
results_df.to_csv(results_path, index=False)

print("\nModel Comparison")
print("----------------")
print(results_df)


# -----------------------------
# Save best model
# -----------------------------
best_model_path = f"{MODEL_DIR}/best_fraud_model.pkl"
joblib.dump(best_pipeline, best_model_path)

print("\nBest Model Selected")
print("-------------------")
print("Best model:", best_model_name)
print("Selection metric: highest recall")
print("Saved to:", best_model_path)


# -----------------------------
# Save feature list
# -----------------------------
feature_info = pd.DataFrame({
    "feature": features,
    "type": ["numeric" if f in numeric_features else "categorical" for f in features]
})

feature_info.to_csv(f"{REPORT_DIR}/model_features.csv", index=False)

print("\nSaved:")
print(results_path)
print(f"{REPORT_DIR}/model_features.csv")
print(best_model_path)
print("\nStep 6 completed successfully.")
