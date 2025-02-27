from abc import ABC, abstractmethod
import pandas as pd
from datetime import timedelta
from app.config import FRAUDULENT_MERCHANTS, WHITELIST_MERCHANTS, USER_CREDIT_LIMITS

class FraudRule(ABC):
    """Base class for all fraud detection rules."""

    @abstractmethod
    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """Look for suspicious transactions and flag them."""
        pass


class HighAmountRule(FraudRule):
    """Flags transactions that exceed an unusually high amount threshold - $10000"""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        # Set the threshold to an unusually high amount (e.g., $10,000)
        threshold = 10000
        return transactions[transactions["amount"] > threshold]

class TotalSpendingRule(FraudRule):
    """Flags users who spend over $50000 in a 24-hour period."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamp to datetime for better processing
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        # Sort transactions by user and time to check for spending over time
        transactions = transactions.sort_values(by=["user_id", "timestamp"])

        # Calculate 24-hour spending for each user
        def calculate_24h_spent(group):
            group = group.copy()  # Avoid warnings by making a copy
            group = group.set_index("timestamp")
            group["24h_spent"] = group["amount"].rolling("1d", min_periods=1).sum()
            return group.reset_index()

        # Apply the spending calculation per user
        transactions = transactions.groupby("user_id", group_keys=False).apply(calculate_24h_spent)

        # Flag transactions where the 24-hour spending exceeds $5000
        flagged_transactions = transactions[transactions["24h_spent"] > 50000]

        return flagged_transactions


class FraudulentMerchantRule(FraudRule):
    """Flags transactions that are made at known fraudulent merchants."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        return transactions[transactions["merchant_name"].isin(FRAUDULENT_MERCHANTS)]


# class MerchantMismatchRule(FraudRule):
#     """Flags users making transactions with new merchants they’ve never interacted with before."""

#     def __init__(self):
#         self.past_merchants = {}  # Keep track of past merchants for each user

#     def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
#         def is_new_merchant(row):
#             user_id, merchant_name = row["user_id"], row["merchant_name"]
#             if user_id not in self.past_merchants:
#                 self.past_merchants[user_id] = set()
#             is_new = merchant_name not in self.past_merchants[user_id]
#             self.past_merchants[user_id].add(merchant_name)
#             return is_new

#         transactions["new_merchant_flag"] = transactions.apply(is_new_merchant, axis=1)
#         return transactions[transactions["new_merchant_flag"]]


class HighTransactionCountRule(FraudRule):
    """Flags users who make too many transactions in a short amount of time."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamp to datetime for easy calculations
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])
        
        # Sort by user and time so we can count transactions per user
        transactions = transactions.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)
        
        results = []  # Store the flagged transactions in a list
        
        # Go through transactions for each user
        for user, group in transactions.groupby("user_id"):
            user_transactions = group.to_dict('records')
            n = len(user_transactions)
            left = 0
            for i in range(n):
                current_time = user_transactions[i]["timestamp"]
                # Slide the left pointer to find transactions within the last hour
                while left < i and (current_time - user_transactions[left]["timestamp"]) > timedelta(hours=1):
                    left += 1
                # Count all transactions in the last hour (inclusive)
                txn_count = i - left + 1
                user_transactions[i]["txn_count"] = txn_count
            results.extend(user_transactions)
        
        result_df = pd.DataFrame(results)
        
        # Flag transactions if there are more than 10 in an hour
        flagged = result_df[result_df["txn_count"] > 10]
        return flagged

class WhitelistMerchantRule(FraudRule):
    """Flags non-whitelisted merchants with excessive transactions within an hour."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        # Focus on transactions made at non-whitelisted merchants
        non_whitelisted = transactions[~transactions["merchant_name"].isin(WHITELIST_MERCHANTS)]
        non_whitelisted = non_whitelisted.copy()

        # Ensure timestamps are in the correct format
        non_whitelisted["timestamp"] = pd.to_datetime(non_whitelisted["timestamp"])

        # Sort by merchant and timestamp to analyze trends
        non_whitelisted = non_whitelisted.sort_values(by=["merchant_name", "timestamp"]).reset_index(drop=True)

        # Initialize a column to count transactions
        non_whitelisted["txn_count"] = 0  

        # Function to calculate the transaction count in the last hour for each merchant
        def count_recent_txns(group):
            txn_counts = []
            for i in range(len(group)):
                start_time = group.iloc[i]["timestamp"] - pd.Timedelta(hours=1)
                txn_counts.append(group[(group["timestamp"] >= start_time) & (group["timestamp"] <= group.iloc[i]["timestamp"])].shape[0])
            group["txn_count"] = txn_counts
            return group

        # Apply the function to each merchant group
        non_whitelisted = non_whitelisted.groupby("merchant_name", group_keys=False).apply(count_recent_txns)

        # Flag transactions if there are 100 or more in the last hour at a non-whitelisted merchant
        flagged_transactions = non_whitelisted[non_whitelisted["txn_count"] >= 100]

        return flagged_transactions


class RapidFireTransactionRule(FraudRule):
    """Flags users who make 5 or more transactions within a 1-minute window."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamps to datetime to perform time calculations
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        # Sort transactions by user and time
        transactions = transactions.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)

        # Initialize transaction count column
        transactions["txn_count"] = 0  

        # Count transactions in the last minute for each user
        def count_recent_txns(group):
            txn_counts = []
            for i in range(len(group)):
                start_time = group.iloc[i]["timestamp"] - pd.Timedelta(minutes=1)
                txn_counts.append(group[(group["timestamp"] >= start_time) & (group["timestamp"] <= group.iloc[i]["timestamp"])].shape[0])
            group["txn_count"] = txn_counts
            return group

        # Apply the function to each user
        transactions = transactions.groupby("user_id", group_keys=False).apply(count_recent_txns)

        # Flag transactions if the count in the last minute is 5 or more
        flagged_transactions = transactions[transactions["txn_count"] >= 5]

        return flagged_transactions


class CreditLimitRule(FraudRule):
    """Flags users whose spending exceeds 30% of their credit limit in a single day."""

    def check(self, transactions: pd.DataFrame) -> pd.DataFrame:
        transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])

        # Sort by user and time to analyze spending
        transactions = transactions.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)

        # Initialize a column for daily spend
        transactions["daily_spend"] = 0  

        # Function to calculate daily spend for each user
        def calculate_24h_spend(group):
            daily_spend_values = []
            for i in range(len(group)):
                start_time = group.iloc[i]["timestamp"] - pd.Timedelta(days=1)
                daily_spend_values.append(group[(group["timestamp"] >= start_time) & 
                                                (group["timestamp"] <= group.iloc[i]["timestamp"])]["amount"].sum())
            group["daily_spend"] = daily_spend_values
            return group

        # Apply the spend calculation per user
        transactions = transactions.groupby("user_id", group_keys=False).apply(calculate_24h_spend)

        # Function to check if daily spend exceeds 30% of the credit limit
        def exceeds_credit_limit(row):
            user_limit = USER_CREDIT_LIMITS.get(row["user_id"], 5000)  # Default to $5000 if no limit set
            return row["daily_spend"] > (0.3 * user_limit)

        # Flag transactions where the daily spend exceeds the limit
        flagged_transactions = transactions[transactions.apply(exceeds_credit_limit, axis=1)]

        return flagged_transactions
