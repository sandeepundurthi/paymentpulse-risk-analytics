# 💳 PaymentPulse: Payment Risk Analytics Platform

PaymentPulse is an end-to-end payment risk analytics platform designed to simulate how banks, fintech companies, and payment processors monitor transaction health, detect fraud, analyze failures, and prioritize risky activity.

The project combines **data engineering, SQL analytics, rule-based risk scoring, machine learning fraud prediction, and an interactive Streamlit dashboard**.

---

# 🚀 Project Objective

Modern payment organizations need to answer questions like:

- What is the payment approval rate?
- Why are transactions failing?
- Which merchants are risky?
- Which channels have higher fraud exposure?
- Which transactions need immediate review?
- How can fraud be predicted proactively?

PaymentPulse solves these challenges using analytics and machine learning.

---

# 📌 Key Features

## ✅ Data Engineering

- Generated **100,000 realistic payment transactions**
- Built raw → cleaned → analytics-ready data pipeline
- Created reusable structured datasets

## ✅ SQL Analytics

Created reporting tables for:

- Daily payment KPIs
- Merchant risk summary
- Failure reason analysis
- Hourly fraud trends
- Location risk exposure

## ✅ Risk Scoring Engine

Each transaction receives:

- `risk_score`
- `risk_level`
- `risk_reason`

Risk levels:

- Low Risk
- Medium Risk
- High Risk
- Critical Risk

## ✅ Machine Learning Fraud Detection

Compared:

- Logistic Regression
- Random Forest
- XGBoost

Final model selected using recall-first strategy.

## ✅ Interactive Dashboard

Built with Streamlit:

- KPI cards
- Fraud trends
- Failure reasons
- Merchant risk table
- Risk distribution
- Live fraud prediction tool

---

# 🛠 Tech Stack

## Languages & Libraries

- Python
- SQL
- SQLite
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Plotly
- Streamlit
- Joblib

---

# 📊 Dataset Summary

| Metric | Value |
|-------|------|
| Transactions | 100,000 |
| Payment Volume | $5.48M+ |
| Approval Rate | 92.31% |
| Failure Rate | 7.69% |
| Fraud Rate | 4.05% |
| Chargeback Rate | 1.93% |

---

# 🤖 Machine Learning Results

| Model | Accuracy | Precision | Recall | ROC-AUC |
|------|----------|----------|--------|--------|
| Logistic Regression | 99.90% | 97.59% | 100% | 1.00 |
| Random Forest | 99.53% | 89.59% | 100% | 0.9999 |
| XGBoost | 100% | 99.88% | 100% | 1.00 |

### Final Selected Model

**Logistic Regression**

Why selected:

- Perfect recall
- Fast
- Explainable
- Finance-friendly
- Easy to audit

---

# 📈 Risk Scoring Results

| Risk Level | Transactions |
|-----------|-------------|
| Critical Risk | 713 |
| High Risk | 1,807 |
| Medium Risk | 7,487 |
| Low Risk | 89,993 |

---

# 📷 Dashboard Screens

Includes:

- Executive KPI overview
- Fraud by payment channel
- Failure reason analysis
- Risk level pie chart
- Hourly fraud trend
- High-risk merchants
- Live prediction tool

---

# 📂 Project Structure

```bash
PaymentPulse/
│── data/
│   ├── raw/
│   ├── processed/
│   └── paymentpulse.db
│
│── src/
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── build_database.py
│   ├── risk_scoring.py
│   └── train_model.py
│
│── dashboard/
│   └── app.py
│
│── reports/
│── models/
│── README.md
```

---
⚙️ How to Run This Project

1️⃣ Clone Repository

git clone https://github.com/yourusername/paymentpulse.git

cd paymentpulse
---
2️⃣ Install Dependencies

pip install -r requirements.txt

or manually:

pip install pandas numpy scikit-learn xgboost streamlit plotly joblib
---
3️⃣ Generate Dataset

python src/generate_data.py
---
4️⃣ Clean Data

python src/clean_data.py
---
5️⃣ Build SQL Database

python src/build_database.py
---
6️⃣ Run Risk Scoring

python src/risk_scoring.py
---
7️⃣ Train Fraud Model

python src/train_model.py
---
8️⃣ Launch Dashboard

streamlit run dashboard/app.py
---
🎯 Business Value

PaymentPulse helps organizations:

Detect fraud faster
Prioritize risky transactions
Reduce chargebacks
Improve approval rates
Identify failing payment patterns
Monitor merchant risk
Improve payment operations efficiency
🔮 Future Improvements
SHAP explainability
Real-time FastAPI fraud API
Kafka streaming transactions
Cloud deployment (AWS/GCP)
Alert system for fraud spikes
Auto retraining pipeline
---
👨‍💻 Author

Sandeep Undurthi

MS Computer Science | Data Science | Analytics | Machine Learning
