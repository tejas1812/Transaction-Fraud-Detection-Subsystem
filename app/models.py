from datetime import datetime
from pydantic import BaseModel

# Not needed right now
class Transaction(BaseModel):
    """Represents a financial transaction."""
    user_id: str
    timestamp: datetime
    merchant_name: str
    amount: float


# Model for adding/removing fraudulent merchant
class MerchantRequest(BaseModel):
    merchant_name: str

# Model for updating user credit limit
class UserCreditLimitRequest(BaseModel):
    user_id: str
    credit_limit: float

# Model for detecting fraud (you could expand this if more data is needed)
class FraudDetectionRequest(BaseModel):
    file: str  # This could be adjusted depending on how the file is sent
