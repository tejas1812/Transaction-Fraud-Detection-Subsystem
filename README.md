# 🚀 Transaction-Fraud-Detection-Subsystem

This microservice detects potentially fraudulent transactions based on multiple fraud detection rules. It ingests transaction data and flags suspicious activities using a rule-based system.

## 📂 Table of Contents
- [Assumptions](#assumptions)
- [Overview](#overview)
- [Fraud Detection Rules](#fraud-detection-rules)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Example Input & Output](#example-input--output)
- [Next Steps](#next-steps)
- [License](#license)

---

## ✅ Assumptions

- The system processes transactions in **batches** rather than real-time streaming.
- Transaction data is provided in **CSV format**.
- Each transaction record contains at least **amount, merchant, user ID, and timestamp**.
- Fraud detection rules operate **independently** and are **composable**.
- Credit limits for users are **predefined** and accessible.
- The system does **not** automatically block transactions but **flags them** for review.
- A **fraudulent merchant list** and a **trusted merchant whitelist** are maintained externally and updated periodically.
- Prioritize minimizing **false negatives**, ensuring suspicious transactions are not missed, even at the cost of flagging some legitimate transactions.
- As the input list is **max 1k in size**, scalability is **not the main focus** of this project.

---

## 🔍 Overview

The subsystem analyzes transaction records and applies a set of fraud rules to identify suspicious transactions. The system is **modular**, allowing easy addition of new fraud rules.

**🚀 Features:**
- Reads transactions from a CSV file
- Applies multiple fraud detection rules
- Flags transactions that match fraud criteria
- Outputs suspicious transactions in JSON format

---

## ⚠️ Fraud Detection Rules

### **1. High Amount Rule**
   - **Description:** Flags transactions that exceed an **unusually high amount threshold** (e.g., $10,000).
   - **Reason:** Unusually large transactions are often fraudulent or unauthorized.
   - **Example Scenario:**  
     A user makes a purchase of **$20,000** from an electronics store. Since the threshold is set at **$10,000**, this transaction is flagged as suspicious due to its high amount.

### **2. Total Spending Rule**
   - **Description:** Flags users whose total spending exceeds **$50,000 within a 24-hour period**.
   - **Reason:** Fraudsters often attempt to maximize purchases before detection.
   - **Example Scenario:**  
    A scenario reflects a case where the user makes eight **$7,000** transactions in a single day, far exceeding the **$50,000** threshold for suspicious spending within a 24-hour period.

### **3. Fraudulent Merchant Rule**
   - **Description:** Flags transactions involving merchants from a **predefined fraud list** (e.g., `ScamStore`, `FakeElectronics`).
   - **Reason:** Some merchants are known for fraudulent activities.
   - **Example Scenario:**  
     A user purchases a product from `ScamStore`, a merchant listed on the fraudulent merchant list. This transaction is flagged because it was made with a known fraudulent merchant.

### **4. High Transaction Count Rule**
   - **Description:** Flags users who make **more than 10 transactions within an hour**.
   - **Reason:** A high volume of transactions in a short period can indicate fraud or account takeover.
   - **Example Scenario:**  
     A user makes **12** small transactions within a span of **30 minutes**. This unusual behavior of high transaction frequency is flagged as suspicious.

### **5. Whitelist Merchant Rule**
   - **Description:** Flags merchants **not on a trusted whitelist** if they receive **more than 5 transactions within a short timespan**.
   - **Reason:** Legitimate merchants like `Amazon` and `Walmart` process many transactions daily, but small unknown merchants should not.
   - **Example Scenario:**  
     A user purchases from **UnknownShop** (not on the whitelist) **7 times in 15 minutes**. This is flagged as suspicious because the merchant receives more transactions than usual within a short period. The user may have **gotten a hold of user credentials from a leak or hack on the dark web**, leading to a potential fraud attempt using stolen credentials.

### **6. Credit History Rule**
   - **Description:** Flags users whose **daily spending exceeds 30% of their estimated credit limit**.
   - **Reason:** Users typically don’t exceed a third of their credit limit in a single day.
   - **Example Scenario:**  
     A user with a credit limit of **$5,000** spends **$1,800** in a single day. Since this exceeds **30%** of the credit limit, it triggers a flag for potentially excessive spending.

### **7. Rapid Fire Transaction Rule**
   - **Description:** Flags users who make **5 or more transactions within 1 minute**.
   - **Reason:** Bots or fraudsters often attempt quick successive transactions to test stolen cards.
   - **Example Scenario:**  
     A user rapidly makes **5 purchases** within **30 seconds** at various online stores. This is flagged as suspicious because the transactions are unusually fast for a real user.

---

## ⚙️ Installation & Setup

### **Prerequisites**
- Python 3.8+
- Pandas library

### **Installation**
1. Clone the repository:
2. Build and run the fraud_detector service 

### **Docker Commands**
To build and run the service using Docker, use the following commands:

```bash
docker build -t fraud_detector .
docker run -p 8000:8000 fraud_detector
```

---

## 🔗 API Endpoints

### **1. Add Fraudulent Merchant**
```bash
curl -X POST "http://localhost:8000/fraud_merchant/add" -H "Content-Type: application/json" -d '{"merchant_name": "ScamStore"}'
```

### **2. Remove Fraudulent Merchant**
```bash
curl -X POST "http://localhost:8000/fraud_merchant/remove" -H "Content-Type: application/json" -d '{"merchant_name": "ScamStore"}'
```

### **3. Add Whitelisted Merchant**
```bash
curl -X POST "http://localhost:8000/whitelist_merchant/add" -H "Content-Type: application/json" -d '{"merchant_name": "Amazon"}'
```

### **4. Remove Whitelisted Merchant**
```bash
curl -X POST "http://localhost:8000/whitelist_merchant/remove" -H "Content-Type: application/json" -d '{"merchant_name": "Amazon"}'
```

### **5. Update User Credit Limit**
```bash
curl -X POST "http://localhost:8000/user_credit_limit/update" -H "Content-Type: application/json" -d '{"user_id": "12345", "credit_limit": 10000}'
```

### **6. Detect Fraudulent Transactions**
```bash
curl -X POST "http://localhost:8000/detect_fraud" -F "file=@combined_transactions.csv"
```

---


## ⏭️ Next Steps

- Implement **real-time streaming support** using Apache Kafka or AWS Kinesis.
- Setup **DBs** with indexes appropriate to the usecases for storing data for further analysis and **ORMs** for access
- Enhance fraud detection with **machine learning models** for anomaly detection.
- Integrate **automatic reporting and alerting** via email or messaging.
- Introduce **configurable rules** to allow dynamic fraud rule updates without redeployment.
- Introduce middle ground for transactions which **need verification** ( Commented code contains one of the rules **"MerchantMismatchRule"** which might be appropriate for this use case)

---

## 📜 License

MIT License. See `LICENSE` for details.
