"""Tests for SQLAlchemy ORM models — schema validation."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from finance_assistant.models import (
    AIConversation,
    AIMessage,
    AnomalyEvent,
    Budget,
    BudgetPeriod,
    Category,
    FinancialAccount,
    Transaction,
    User,
    UserCategoryRule,
    UserSession,
)
from finance_assistant.models.base import Base


def test_all_models_have_tablename() -> None:
    """All models should define a __tablename__."""
    for mapper in Base.registry.mappers:
        model = mapper.class_
        assert hasattr(model, "__tablename__"), f"{model.__name__} missing __tablename__"


def test_user_model_defaults() -> None:
    """User model should have correct defaults."""
    user = User(email="test@example.com")
    assert user.subscription_tier == "free"
    assert user.mfa_enabled is False
    assert user.is_active is True
    assert user.is_verified is False
    assert user.data_region == "us-east-1"
    assert user.deleted_at is None


def test_user_repr() -> None:
    """User repr should include id and email."""
    user = User(email="test@example.com")
    user.id = uuid.uuid4()
    repr_str = repr(user)
    assert "User" in repr_str
    assert "test@example.com" in repr_str


def test_financial_account_defaults() -> None:
    """FinancialAccount should have correct defaults."""
    account = FinancialAccount(
        user_id=uuid.uuid4(),
        institution_name="Test Bank",
        account_name="Checking",
        account_type="checking",
    )
    assert account.currency_code == "USD"
    assert account.is_active is True
    assert account.sync_status == "active"


def test_transaction_model_fields() -> None:
    """Transaction should accept all blueprint fields."""
    txn = Transaction(
        user_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        source="plaid",
        amount=42.50,
        description="Starbucks Coffee",
        transaction_date=date(2026, 7, 1),
        category_source="ml",
        category_confidence=0.95,
        tags=["coffee", "daily"],
        location={"city": "New York", "state": "NY"},
    )
    assert txn.amount == 42.50
    assert txn.source == "plaid"
    assert txn.is_pending is False
    assert txn.is_recurring is False
    assert txn.is_excluded is False
    assert txn.tags == ["coffee", "daily"]


def test_category_hierarchy() -> None:
    """Category should support parent-child relationships."""
    parent = Category(name="Food & Dining", slug="food-dining")
    parent.id = 1
    child = Category(name="Coffee Shops", slug="coffee-shops", parent_id=1)
    child.id = 2
    assert child.parent_id == parent.id


def test_budget_defaults() -> None:
    """Budget should have correct alert threshold default."""
    budget = Budget(
        user_id=uuid.uuid4(),
        name="Food Budget",
        amount=500.00,
        period="monthly",
        start_date=date(2026, 7, 1),
    )
    assert budget.alert_at_percent == 80
    assert budget.rollover is False
    assert budget.is_active is True


def test_budget_period_tracking() -> None:
    """BudgetPeriod should track spending against allocation."""
    period = BudgetPeriod(
        budget_id=uuid.uuid4(),
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
        allocated_amount=500.00,
        spent_amount=347.82,
    )
    assert period.allocated_amount == 500.00
    assert period.spent_amount == 347.82
    assert period.alert_50_sent_at is None
    assert period.alert_80_sent_at is None


def test_ai_conversation_defaults() -> None:
    """AIConversation should have zero counts by default."""
    conv = AIConversation(user_id=uuid.uuid4())
    assert conv.message_count == 0
    assert conv.total_tokens_used == 0
    assert conv.total_cost_cents == 0


def test_ai_message_observability() -> None:
    """AIMessage should capture full LLM observability metadata."""
    msg = AIMessage(
        conversation_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="assistant",
        content="Your food spending increased by 40%.",
        model_used="claude-3-5-sonnet",
        provider="bedrock",
        prompt_tokens=1847,
        completion_tokens=342,
        latency_ms=2341,
        cost_cents=0.0045,
        rag_retrieved_chunks=5,
        hallucination_score=0.94,
    )
    assert msg.role == "assistant"
    assert msg.provider == "bedrock"
    assert msg.hallucination_score == 0.94
    assert msg.human_reviewed is False


def test_anomaly_event_defaults() -> None:
    """AnomalyEvent should default to not acknowledged."""
    event = AnomalyEvent(
        user_id=uuid.uuid4(),
        anomaly_type="high_spend",
        severity="medium",
        score=0.78,
    )
    assert event.is_acknowledged is False
    assert event.is_false_positive is None


def test_base_metadata_has_all_tables() -> None:
    """The Base metadata should contain all expected tables."""
    expected_tables = {
        "users",
        "user_sessions",
        "financial_accounts",
        "categories",
        "user_category_rules",
        "transactions",
        "budgets",
        "budget_periods",
        "ai_conversations",
        "ai_messages",
        "anomaly_events",
        "knowledge_embeddings",
        "user_financial_embeddings",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"
