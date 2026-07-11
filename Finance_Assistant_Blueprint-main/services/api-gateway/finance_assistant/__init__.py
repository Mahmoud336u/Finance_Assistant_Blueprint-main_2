"""Finance Assistant Blueprint — Core Package.

Exports the core transaction utilities and the FastAPI application.
"""

from .core import (
    Transaction,
    categorize_transaction,
    dashboard_data,
    generate_budget_suggestions,
    load_transactions_from_csv,
    load_transactions_from_plaid,
    spending_by_category,
)

__all__ = [
    "Transaction",
    "categorize_transaction",
    "dashboard_data",
    "generate_budget_suggestions",
    "load_transactions_from_csv",
    "load_transactions_from_plaid",
    "spending_by_category",
]
