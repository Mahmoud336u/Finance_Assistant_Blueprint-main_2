"""Initial schema — all core tables.

Revision ID: 0001
Revises: None
Create Date: 2026-07-12

Creates all tables from the System Blueprint Section 6.1:
- users, user_sessions
- financial_accounts
- categories, user_category_rules
- transactions
- budgets, budget_periods
- ai_conversations, ai_messages
- anomaly_events
- knowledge_embeddings, user_financial_embeddings (pgvector)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all core tables and enable pgvector extension."""

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("cognito_sub", sa.String(255), unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("subscription_tier", sa.String(20), server_default="free", nullable=False),
        sa.Column("mfa_enabled", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("gdpr_consent_at", sa.DateTime(timezone=True)),
        sa.Column("gdpr_consent_version", sa.String(10)),
        sa.Column("data_region", sa.String(20), server_default="us-east-1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_users_email", "users", ["email"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_users_cognito_sub", "users", ["cognito_sub"])

    # --- user_sessions ---
    op.create_table(
        "user_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("device_fingerprint", sa.String(255)),
        sa.Column("ip_address", INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_sessions_user_id", "user_sessions", ["user_id", "expires_at"],
                     postgresql_where=sa.text("revoked_at IS NULL"))

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("parent_id", sa.Integer),
        sa.Column("icon_url", sa.String(255)),
        sa.Column("color", sa.String(7)),
        sa.Column("is_system", sa.Boolean, server_default="true"),
        sa.Column("is_income", sa.Boolean, server_default="false"),
        sa.Column("sort_order", sa.Integer, server_default="0"),
    )

    # --- Seed default categories ---
    op.execute("""
        INSERT INTO categories (name, slug, is_system, is_income, sort_order) VALUES
        ('Food & Dining', 'food-dining', true, false, 1),
        ('Groceries', 'groceries', true, false, 2),
        ('Rent & Mortgage', 'rent-mortgage', true, false, 3),
        ('Utilities', 'utilities', true, false, 4),
        ('Transportation', 'transportation', true, false, 5),
        ('Entertainment', 'entertainment', true, false, 6),
        ('Shopping', 'shopping', true, false, 7),
        ('Healthcare', 'healthcare', true, false, 8),
        ('Education', 'education', true, false, 9),
        ('Travel', 'travel', true, false, 10),
        ('Insurance', 'insurance', true, false, 11),
        ('Subscriptions', 'subscriptions', true, false, 12),
        ('Personal Care', 'personal-care', true, false, 13),
        ('Gifts & Donations', 'gifts-donations', true, false, 14),
        ('Salary', 'salary', true, true, 15),
        ('Freelance Income', 'freelance-income', true, true, 16),
        ('Investment Income', 'investment-income', true, true, 17),
        ('Other Income', 'other-income', true, true, 18),
        ('Other', 'other', true, false, 99)
    """)

    # --- user_category_rules ---
    op.create_table(
        "user_category_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern", sa.String(500), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("match_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_rules_user", "user_category_rules", ["user_id"],
                     postgresql_where=sa.text("is_active = TRUE"))

    # --- financial_accounts ---
    op.create_table(
        "financial_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plaid_account_id", sa.String(255)),
        sa.Column("plaid_item_id", sa.String(255)),
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column("account_subtype", sa.String(50)),
        sa.Column("mask", sa.String(10)),
        sa.Column("currency_code", sa.String(3), server_default="USD"),
        sa.Column("current_balance", sa.Numeric(15, 2)),
        sa.Column("available_balance", sa.Numeric(15, 2)),
        sa.Column("balance_updated_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("sync_status", sa.String(20), server_default="active"),
        sa.Column("sync_error_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_accounts_user_id", "financial_accounts", ["user_id"],
                     postgresql_where=sa.text("is_active = TRUE"))
    op.create_index("idx_accounts_plaid", "financial_accounts", ["plaid_item_id", "plaid_account_id"])

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("financial_accounts.id"), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency_code", sa.String(3), server_default="USD"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("merchant_name", sa.String(255)),
        sa.Column("merchant_category_code", sa.String(10)),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id")),
        sa.Column("category_confidence", sa.Numeric(3, 2)),
        sa.Column("category_source", sa.String(20)),
        sa.Column("is_pending", sa.Boolean, server_default="false"),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("posted_date", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("tags", ARRAY(sa.Text)),
        sa.Column("is_recurring", sa.Boolean, server_default="false"),
        sa.Column("recurrence_group_id", UUID(as_uuid=True)),
        sa.Column("is_excluded", sa.Boolean, server_default="false"),
        sa.Column("fingerprint", sa.String(64), unique=True),
        sa.Column("location", JSONB),
        sa.Column("raw_metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_txn_user_date", "transactions", ["user_id", sa.text("transaction_date DESC")])
    op.create_index("idx_txn_user_category", "transactions",
                     ["user_id", "category_id", sa.text("transaction_date DESC")])
    op.create_index("idx_txn_account", "transactions", ["account_id", sa.text("transaction_date DESC")])
    op.create_index("idx_txn_fingerprint", "transactions", ["fingerprint"])
    op.create_index("idx_txn_merchant", "transactions", ["user_id", "merchant_name"])

    # --- budgets ---
    op.create_table(
        "budgets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id")),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date),
        sa.Column("rollover", sa.Boolean, server_default="false"),
        sa.Column("alert_at_percent", sa.Integer, server_default="80"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_budgets_user", "budgets", ["user_id"],
                     postgresql_where=sa.text("is_active = TRUE"))

    # --- budget_periods ---
    op.create_table(
        "budget_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("budget_id", UUID(as_uuid=True), sa.ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("allocated_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("spent_amount", sa.Numeric(15, 2), server_default="0"),
        sa.Column("alert_50_sent_at", sa.DateTime(timezone=True)),
        sa.Column("alert_80_sent_at", sa.DateTime(timezone=True)),
        sa.Column("alert_100_sent_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("budget_id", "period_start", name="uq_budget_period"),
    )

    # --- ai_conversations ---
    op.create_table(
        "ai_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_message_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("total_tokens_used", sa.Integer, server_default="0"),
        sa.Column("total_cost_cents", sa.Integer, server_default="0"),
    )

    # --- ai_messages ---
    op.create_table(
        "ai_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", UUID(as_uuid=True),
                   sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_sanitized", sa.Text),
        sa.Column("model_used", sa.String(100)),
        sa.Column("provider", sa.String(50)),
        sa.Column("prompt_tokens", sa.Integer),
        sa.Column("completion_tokens", sa.Integer),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("cost_cents", sa.Numeric(8, 4)),
        sa.Column("rag_retrieved_chunks", sa.Integer),
        sa.Column("hallucination_score", sa.Numeric(3, 2)),
        sa.Column("human_reviewed", sa.Boolean, server_default="false"),
        sa.Column("review_outcome", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_ai_messages_conversation", "ai_messages", ["conversation_id", "created_at"])
    op.create_index("idx_ai_messages_user", "ai_messages", ["user_id", sa.text("created_at DESC")])

    # --- anomaly_events ---
    op.create_table(
        "anomaly_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("transaction_id", UUID(as_uuid=True)),
        sa.Column("anomaly_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("score", sa.Numeric(5, 4)),
        sa.Column("metadata", JSONB),
        sa.Column("is_acknowledged", sa.Boolean, server_default="false"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("is_false_positive", sa.Boolean),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_anomaly_user", "anomaly_events", ["user_id", sa.text("created_at DESC")],
                     postgresql_where=sa.text("NOT is_acknowledged"))

    # --- knowledge_embeddings (pgvector) ---
    op.create_table(
        "knowledge_embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", JSONB),
        sa.Column("embedding_model_version", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Vector column added via raw SQL (Alembic doesn't natively support pgvector)
    op.execute("ALTER TABLE knowledge_embeddings ADD COLUMN embedding vector(1024)")
    op.execute("""
        CREATE INDEX idx_knowledge_embedding ON knowledge_embeddings
        USING hnsw (embedding vector_cosine_ops)
    """)

    # --- user_financial_embeddings (pgvector) ---
    op.create_table(
        "user_financial_embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary_type", sa.String(50), nullable=False),
        sa.Column("period_start", sa.Date),
        sa.Column("period_end", sa.Date),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding_model_version", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.execute("ALTER TABLE user_financial_embeddings ADD COLUMN embedding vector(1024)")
    op.execute("""
        CREATE INDEX idx_user_financial_embedding ON user_financial_embeddings
        USING hnsw (embedding vector_cosine_ops)
    """)
    op.create_index("idx_user_financial_user", "user_financial_embeddings", ["user_id", "summary_type"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("user_financial_embeddings")
    op.drop_table("knowledge_embeddings")
    op.drop_table("anomaly_events")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("budget_periods")
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("financial_accounts")
    op.drop_table("user_category_rules")
    op.drop_table("categories")
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
