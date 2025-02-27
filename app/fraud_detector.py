import pandas as pd
import numpy as np
from app.fraud_rules import (
    HighAmountRule,
    TotalSpendingRule,
    FraudulentMerchantRule,
    # MerchantMismatchRule,
    HighTransactionCountRule,
    WhitelistMerchantRule,
    RapidFireTransactionRule,
    CreditLimitRule,
)
import uuid


class FraudDetector:
    """Handles fraud detection by applying a variety of fraud rules to transaction data."""

    def __init__(self):
        # Initialize the fraud detection rules we want to use
        self.rules = [
            HighAmountRule(),
            TotalSpendingRule(),
            FraudulentMerchantRule(),
            # MerchantMismatchRule(),
            HighTransactionCountRule(),
            WhitelistMerchantRule(),
            RapidFireTransactionRule(),
            CreditLimitRule(),
        ]

    def detect_fraud(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """
        Applies all fraud detection rules to a set of transactions and flags suspicious ones.

        :param transactions: A Pandas DataFrame containing transaction data
        :return: A DataFrame of flagged suspicious transactions, with the reasons for flags
        """
        flagged_transaction_map = {}  # Keeps track of transaction IDs and the reasons they were flagged

        # If the transactions don't already have a unique transaction ID, generate one
        if "transaction_id" not in transactions.columns:
            transactions["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(transactions))]

        # Fill any missing data with "Unknown" to avoid errors during rule checks
        transactions.fillna("Unknown", inplace=True)

        # Loop through all fraud detection rules
        for rule in self.rules:
            fraud_cases = rule.check(transactions)
            if not fraud_cases.empty:
                fraud_reason = rule.__class__.__name__  # Get the name of the rule that flagged the transaction
                for txn_id in fraud_cases["transaction_id"]:
                    # Add the fraud reason to the transaction's record
                    if txn_id not in flagged_transaction_map:
                        flagged_transaction_map[txn_id] = []
                    flagged_transaction_map[txn_id].append(fraud_reason)

        # Extract the full transaction records that were flagged
        flagged_transactions = transactions[transactions["transaction_id"].isin(flagged_transaction_map.keys())].copy()

        # Add a new column to show the reasons each transaction was flagged for fraud
        flagged_transactions["fraud_reasons"] = flagged_transactions["transaction_id"].map(flagged_transaction_map)

        # Handle any infinite or missing values in the flagged transactions
        flagged_transactions.replace([np.inf, -np.inf], np.nan, inplace=True)
        flagged_transactions.fillna("Unknown", inplace=True)
        print(len(flagged_transactions))  # Print the number of flagged transactions

        # Return the final list of flagged transactions with reasons
        return flagged_transactions.reset_index(drop=True)