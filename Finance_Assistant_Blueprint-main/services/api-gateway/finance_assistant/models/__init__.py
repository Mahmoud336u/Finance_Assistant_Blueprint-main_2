"""Meridian — Database Models Package.

SQLAlchemy 2.0 async-compatible ORM models mapping the blueprint's
PostgreSQL schema (System Blueprint Section 6.1).
"""

from .base import Base, TimestampMixin, UUIDMixin
from .user import User, UserSession
from .account import FinancialAccount
from .category import Category, UserCategoryRule
from .transaction import Transaction
from .budget import Budget, BudgetPeriod
from .ai import AIConversation, AIMessage
from .anomaly import AnomalyEvent
from .embedding import KnowledgeEmbedding, UserFinancialEmbedding

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "User",
    "UserSession",
    "FinancialAccount",
    "Category",
    "UserCategoryRule",
    "Transaction",
    "Budget",
    "BudgetPeriod",
    "AIConversation",
    "AIMessage",
    "AnomalyEvent",
    "KnowledgeEmbedding",
    "UserFinancialEmbedding",
]
