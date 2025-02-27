# config.py - Mock storage

# Fraudulent merchant list - Ideally in memory - Redis
FRAUDULENT_MERCHANTS = {"ScamStore", "FakeElectronics", "ShadyBank"}

# Whitelisted merchants (trusted large-scale businesses) -  - Ideally in memory - Redis
WHITELIST_MERCHANTS = {"Amazon", "Walmart", "BestBuy", "Target", "Apple Store", "Netflix", "McDonald's", "Uber", "eBay"}

# User credit scores mapping (user_id -> credit limit) - DB
USER_CREDIT_LIMITS = {
    "U123": 10000,
    "U234": 5000,
    "U345": 7000,
    "U456": 15000
}
