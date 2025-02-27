# main.py

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from app.models import MerchantRequest, UserCreditLimitRequest, FraudDetectionRequest
from app.fraud_detector import FraudDetector
from app.config import FRAUDULENT_MERCHANTS, WHITELIST_MERCHANTS, USER_CREDIT_LIMITS
import pandas as pd
import threading
import json
from fastapi.responses import JSONResponse

app = FastAPI()
fraud_detector = FraudDetector()
lock = threading.Lock()

### Fraudulent Merchant Management
@app.post("/fraud_merchant/add")
def add_fraud_merchant(request: MerchantRequest):
    merchant_name = request.merchant_name
    if not merchant_name:
        raise HTTPException(status_code=400, detail="Merchant name required")
    
    with lock:
        FRAUDULENT_MERCHANTS.add(merchant_name)
    return {"message": f"Merchant {merchant_name} added to fraud list"}

@app.post("/fraud_merchant/remove")
def remove_fraud_merchant(request: MerchantRequest):
    merchant_name = request.merchant_name
    if not merchant_name:
        raise HTTPException(status_code=400, detail="Merchant name required")
    
    with lock:
        if merchant_name not in FRAUDULENT_MERCHANTS:
            raise HTTPException(status_code=400, detail="Merchant not found in fraud list")
        FRAUDULENT_MERCHANTS.remove(merchant_name)
    
    return {"message": f"Merchant {merchant_name} removed from fraud list"}

### 🔹 Whitelisted Merchant Management
@app.post("/whitelist_merchant/add")
def add_whitelist_merchant(request: MerchantRequest):
    merchant_name = request.merchant_name
    if not merchant_name:
        raise HTTPException(status_code=400, detail="Merchant name required")
    
    with lock:
        WHITELIST_MERCHANTS.add(merchant_name)
    return {"message": f"Merchant {merchant_name} added to whitelist"}

@app.post("/whitelist_merchant/remove")
def remove_whitelist_merchant(request: MerchantRequest):
    merchant_name = request.merchant_name
    if not merchant_name:
        raise HTTPException(status_code=400, detail="Merchant name required")
    
    with lock:
        if merchant_name not in WHITELIST_MERCHANTS:
            raise HTTPException(status_code=400, detail="Merchant not found in whitelist")
        WHITELIST_MERCHANTS.remove(merchant_name)
    
    return {"message": f"Merchant {merchant_name} removed from whitelist"}

### User Credit Score Management
@app.post("/user_credit_limit/update")
def update_user_credit_limit(request: UserCreditLimitRequest):
    user_id = request.user_id
    credit_limit = request.credit_limit
    if not user_id or credit_limit <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID or credit limit")
    
    with lock:
        USER_CREDIT_LIMITS[user_id] = credit_limit
    
    return {"message": f"Credit limit updated for user {user_id}"}

### Fraud Detection
@app.post("/detect_fraud")
def detect_fraud(file: UploadFile = File(...)):
    try:
        transactions = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file format")
    
    flagged_transactions = fraud_detector.detect_fraud(transactions)    
    
    # Convert Timestamp columns to strings
    flagged_transactions["timestamp"] = flagged_transactions["timestamp"].astype(str)
    
    # Convert DataFrame to a list of dictionaries and format it as a pretty JSON string
    response_data = flagged_transactions.to_dict(orient="records")

    
    return JSONResponse(content=response_data)
