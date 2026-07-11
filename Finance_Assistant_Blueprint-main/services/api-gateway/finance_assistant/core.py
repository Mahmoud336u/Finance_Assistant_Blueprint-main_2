from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import csv
from io import StringIO
from typing import Iterable


CATEGORY_KEYWORDS = {
    "Food": {"restaurant", "cafe", "coffee", "food", "grocer", "supermarket", "uber eats"},
    "Rent": {"rent", "landlord", "apartment", "lease", "property"},
    "Entertainment": {"movie", "cinema", "spotify", "netflix", "concert", "game"},
    "Transport": {"uber", "lyft", "taxi", "metro", "fuel", "gas"},
    "Utilities": {"electric", "water", "internet", "utility", "phone", "wifi"},
}


@dataclass(frozen=True)
class Transaction:
    date: str
    description: str
    amount: float
    category: str


def categorize_transaction(description: str) -> str:
    text = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def _normalize_transaction(date: str, description: str, amount: float, category: str | None = None) -> Transaction:
    clean_category = category or categorize_transaction(description)
    return Transaction(date=date, description=description, amount=float(amount), category=clean_category)


def load_transactions_from_csv(csv_content: str) -> list[Transaction]:
    reader = csv.DictReader(StringIO(csv_content))
    required = {"date", "description", "amount"}
    if not reader.fieldnames or not required.issubset({name.strip().lower() for name in reader.fieldnames}):
        raise ValueError("CSV must contain date, description, and amount columns")

    normalized: list[Transaction] = []
    for row in reader:
        date = (row.get("date") or "").strip()
        description = (row.get("description") or "").strip()
        amount_text = (row.get("amount") or "").strip()
        category = (row.get("category") or "").strip() or None

        has_context = any((date, description, category))
        if not has_context and not amount_text:
            continue

        if has_context and not amount_text:
            raise ValueError("Each transaction row must include an amount.")

        normalized.append(
            _normalize_transaction(
                date=date,
                description=description,
                amount=float(amount_text),
                category=category,
            )
        )
    return normalized


def load_transactions_from_plaid(plaid_payload: dict) -> list[Transaction]:
    transactions = plaid_payload.get("transactions", [])
    normalized: list[Transaction] = []
    for item in transactions:
        name = item.get("name", "")
        date = item.get("date", "")
        amount = item.get("amount", 0.0)
        category = None
        categories = item.get("category")
        if isinstance(categories, list) and categories:
            category = categories[-1]
        normalized.append(_normalize_transaction(date=date, description=name, amount=amount, category=category))
    return normalized


def spending_by_category(transactions: Iterable[Transaction]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.amount > 0:
            totals[transaction.category] += transaction.amount
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def _monthly_spending(transactions: Iterable[Transaction]) -> dict[str, float]:
    monthly: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        if transaction.amount <= 0:
            continue
        month = datetime.strptime(transaction.date, "%Y-%m-%d").strftime("%Y-%m")
        monthly[month] += transaction.amount
    return dict(sorted(monthly.items()))


def dashboard_data(transactions: Iterable[Transaction]) -> dict:
    by_category = spending_by_category(transactions)
    by_month = _monthly_spending(transactions)
    return {
        "cards": {
            "total_spending": round(sum(by_category.values()), 2),
            "top_category": next(iter(by_category), "None"),
        },
        "charts": {
            "category_breakdown": {
                "type": "pie",
                "labels": list(by_category.keys()),
                "values": [round(v, 2) for v in by_category.values()],
            },
            "monthly_trend": {
                "type": "bar",
                "labels": list(by_month.keys()),
                "values": [round(v, 2) for v in by_month.values()],
            },
        },
    }


def generate_budget_suggestions(transactions: Iterable[Transaction], monthly_income: float) -> list[str]:
    category_totals = spending_by_category(transactions)
    total_spending = sum(category_totals.values())

    suggestions: list[str] = []
    if not category_totals:
        return ["Add transaction data to receive personalized budgeting suggestions."]

    top_category, top_value = next(iter(category_totals.items()))
    suggestions.append(
        f"Your highest spending category is {top_category} (${top_value:.2f}). Consider setting a category cap."
    )

    if monthly_income > 0:
        savings_rate = max((monthly_income - total_spending) / monthly_income, 0)
        if savings_rate < 0.2:
            suggestions.append("Your estimated savings rate is below 20%. Target recurring costs first to improve it.")
        else:
            suggestions.append("Great job—your estimated savings rate is healthy. Keep tracking to maintain momentum.")

    if "Entertainment" in category_totals and category_totals["Entertainment"] > 0.15 * max(monthly_income, 1):
        suggestions.append("Entertainment spending is relatively high; try a weekly discretionary budget.")

    return suggestions
