import sqlite3
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="PaymentPulse Risk Analytics",
    page_icon="💳",
    layout="wide"
)

DB_PATH = "data/paymentpulse.db"
MODEL_PATH = "models/best_fraud_model.pkl"


# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


transactions = load_table("payment_transactions_scored")
daily_kpis = load_table("daily_payment_kpis")
merchant_risk = load_table("merchant_risk_summary")
failure_summary = load_table("failure_reason_summary")
hourly_risk = load_table("hourly_risk_summary")

model = load_model()


# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.title("Filters")

merchant_categories = ["All"] + sorted(transactions["merchant_category"].unique().tolist())
channels = ["All"] + sorted(transactions["channel"].unique().tolist())
payment_methods = ["All"] + sorted(transactions["payment_method"].unique().tolist())

selected_category = st.sidebar.selectbox("Merchant Category", merchant_categories)
selected_channel = st.sidebar.selectbox("Channel", channels)
selected_payment_method = st.sidebar.selectbox("Payment Method", payment_methods)

filtered_df = transactions.copy()

if selected_category != "All":
    filtered_df = filtered_df[filtered_df["merchant_category"] == selected_category]

if selected_channel != "All":
    filtered_df = filtered_df[filtered_df["channel"] == selected_channel]

if selected_payment_method != "All":
    filtered_df = filtered_df[filtered_df["payment_method"] == selected_payment_method]


# -----------------------------
# Header
# -----------------------------
st.title("💳 PaymentPulse: Payment Risk Analytics Dashboard")

st.markdown(
    """
    This dashboard analyzes payment transactions, fraud indicators, chargebacks, failed payments,
    merchant risk, and transaction-level risk scoring.
    """
)


# -----------------------------
# KPI Cards
# -----------------------------
total_transactions = len(filtered_df)
total_volume = filtered_df["transaction_amount"].sum()
approval_rate = (filtered_df["transaction_status"].eq("Approved").mean()) * 100
failure_rate = (filtered_df["transaction_status"].eq("Failed").mean()) * 100
fraud_rate = filtered_df["is_fraud"].mean() * 100
chargeback_rate = filtered_df["is_chargeback"].mean() * 100

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric("Total Transactions", f"{total_transactions:,}")
col2.metric("Total Payment Volume", f"${total_volume:,.2f}")
col3.metric("Approval Rate", f"{approval_rate:.2f}%")
col4.metric("Failure Rate", f"{failure_rate:.2f}%")
col5.metric("Fraud Rate", f"{fraud_rate:.2f}%")
col6.metric("Chargeback Rate", f"{chargeback_rate:.2f}%")


st.divider()


# -----------------------------
# Charts Row 1
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Fraud Rate by Channel")
    fraud_channel = (
        filtered_df.groupby("channel")
        .agg(
            total_transactions=("transaction_id", "count"),
            fraud_transactions=("is_fraud", "sum")
        )
        .reset_index()
    )
    fraud_channel["fraud_rate_pct"] = (
        fraud_channel["fraud_transactions"] / fraud_channel["total_transactions"] * 100
    )

    fig = px.bar(
        fraud_channel,
        x="channel",
        y="fraud_rate_pct",
        text="fraud_rate_pct",
        title="Fraud Rate by Payment Channel"
    )
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Failure Reasons")
    failed_df = filtered_df[filtered_df["transaction_status"] == "Failed"]

    failure_counts = (
        failed_df["failure_reason"]
        .value_counts()
        .reset_index()
    )
    failure_counts.columns = ["failure_reason", "count"]

    fig = px.bar(
        failure_counts,
        x="count",
        y="failure_reason",
        orientation="h",
        title="Top Payment Failure Reasons"
    )
    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Charts Row 2
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Risk Level Distribution")
    risk_dist = (
        filtered_df["risk_level"]
        .value_counts()
        .reset_index()
    )
    risk_dist.columns = ["risk_level", "transactions"]

    fig = px.pie(
        risk_dist,
        names="risk_level",
        values="transactions",
        title="Transaction Risk Level Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Hourly Fraud Trend")
    hourly = (
        filtered_df.groupby("hour")
        .agg(
            total_transactions=("transaction_id", "count"),
            fraud_transactions=("is_fraud", "sum")
        )
        .reset_index()
    )
    hourly["fraud_rate_pct"] = (
        hourly["fraud_transactions"] / hourly["total_transactions"] * 100
    )

    fig = px.line(
        hourly,
        x="hour",
        y="fraud_rate_pct",
        markers=True,
        title="Fraud Rate by Hour"
    )
    st.plotly_chart(fig, use_container_width=True)


st.divider()


# -----------------------------
# High Risk Merchant Table
# -----------------------------
st.subheader("Top High-Risk Merchants")

high_risk_merchants = merchant_risk[
    merchant_risk["merchant_risk_level"] == "High Risk"
].sort_values(
    by=["fraud_rate_pct", "chargeback_rate_pct", "failure_rate_pct"],
    ascending=False
)

st.dataframe(
    high_risk_merchants.head(25),
    use_container_width=True
)


st.divider()


# -----------------------------
# Transaction Risk Checker
# -----------------------------
st.subheader("Live Fraud Prediction Demo")

st.markdown(
    """
    Enter transaction details below to predict whether a transaction is likely fraudulent.
    """
)

with st.form("prediction_form"):

    col1, col2, col3 = st.columns(3)

    with col1:
        transaction_amount = st.number_input(
            "Transaction Amount",
            min_value=1.0,
            max_value=5000.0,
            value=100.0
        )

        processor_response_ms = st.number_input(
            "Processor Response Time (ms)",
            min_value=80,
            max_value=3000,
            value=450
        )

        hour = st.slider("Hour of Day", 0, 23, 12)

    with col2:
        month = st.slider("Month", 1, 12, 6)

        is_weekend = st.selectbox("Weekend?", [0, 1])

        high_value_txn = 1 if transaction_amount >= 500 else 0
        slow_response = 1 if processor_response_ms >= 900 else 0

    with col3:
        payment_method = st.selectbox(
            "Payment Method",
            sorted(transactions["payment_method"].unique())
        )

        channel = st.selectbox(
            "Channel",
            sorted(transactions["channel"].unique())
        )

        device_type = st.selectbox(
            "Device Type",
            sorted(transactions["device_type"].unique())
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        merchant_category = st.selectbox(
            "Merchant Category",
            sorted(transactions["merchant_category"].unique())
        )

    with col5:
        customer_location = st.selectbox(
            "Customer Location",
            sorted(transactions["customer_location"].unique())
        )

    with col6:
        transaction_status = st.selectbox(
            "Transaction Status",
            sorted(transactions["transaction_status"].unique())
        )

    # Simple risk score logic for prediction input
    risk_score = 0

    if transaction_amount >= 2000:
        risk_score += 30
    elif transaction_amount >= 1000:
        risk_score += 20
    elif transaction_amount >= 500:
        risk_score += 10

    if transaction_status == "Failed":
        risk_score += 15

    if slow_response == 1:
        risk_score += 10

    if channel == "Online":
        risk_score += 8
    elif channel == "Mobile App":
        risk_score += 4

    if merchant_category in ["Travel", "Electronics", "Financial Services"]:
        risk_score += 12

    if customer_location in ["FL", "NV", "NY"]:
        risk_score += 8

    submit = st.form_submit_button("Predict Fraud Risk")

if submit:
    input_df = pd.DataFrame([{
        "transaction_amount": transaction_amount,
        "processor_response_ms": processor_response_ms,
        "hour": hour,
        "month": month,
        "is_weekend": is_weekend,
        "high_value_txn": high_value_txn,
        "slow_response": slow_response,
        "risk_score": risk_score,
        "payment_method": payment_method,
        "channel": channel,
        "device_type": device_type,
        "merchant_category": merchant_category,
        "customer_location": customer_location,
        "transaction_status": transaction_status
    }])

    prediction = model.predict(input_df)[0]

    if hasattr(model, "predict_proba"):
        fraud_probability = model.predict_proba(input_df)[0][1]
    else:
        fraud_probability = None

    if risk_score >= 75:
        rule_risk_level = "Critical Risk"
    elif risk_score >= 50:
        rule_risk_level = "High Risk"
    elif risk_score >= 25:
        rule_risk_level = "Medium Risk"
    else:
        rule_risk_level = "Low Risk"

    st.subheader("Prediction Result")

    col1, col2, col3 = st.columns(3)

    col1.metric("ML Prediction", "Fraud" if prediction == 1 else "Not Fraud")

    if fraud_probability is not None:
        col2.metric("Fraud Probability", f"{fraud_probability * 100:.2f}%")
    else:
        col2.metric("Fraud Probability", "N/A")

    col3.metric("Rule-Based Risk Level", rule_risk_level)

    st.write("Rule-Based Risk Score:", risk_score)


st.divider()


# -----------------------------
# Raw Data Preview
# -----------------------------
st.subheader("Transaction Data Preview")

preview_cols = [
    "transaction_id",
    "transaction_amount",
    "payment_method",
    "channel",
    "merchant_category",
    "customer_location",
    "transaction_status",
    "is_fraud",
    "is_chargeback",
    "risk_score",
    "risk_level"
]

st.dataframe(
    filtered_df[preview_cols].head(100),
    use_container_width=True
)
