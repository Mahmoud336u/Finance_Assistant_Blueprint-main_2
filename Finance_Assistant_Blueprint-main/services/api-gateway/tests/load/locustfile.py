"""Meridian — Load Testing with Locust.

Performance test suite targeting the p99 < 2s SLO.
Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from __future__ import annotations

import json
import os
import random
import uuid

from locust import HttpUser, between, task

# Test API key for service-to-service auth
API_KEY = os.getenv("TEST_API_KEY", "dev-ingestion-key-2026")


class MeridianAPIUser(HttpUser):
    """Simulates a typical user interacting with the Meridian API."""

    wait_time = between(1, 5)
    abstract = True

    def on_start(self):
        """Set up common headers."""
        self.headers = {
            "Content-Type": "application/json",
        }
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_test_token()}",
        }
        self.api_key_headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
        }

    def _get_test_token(self) -> str:
        """Get a test JWT token (would be from Cognito in real tests)."""
        return os.getenv("TEST_JWT_TOKEN", "test-token")


class HealthCheckUser(MeridianAPIUser):
    """Load test focused on health/readiness endpoints."""

    weight = 1

    @task(5)
    def check_health(self):
        """GET /health — liveness probe."""
        self.client.get("/health", name="/health")

    @task(3)
    def check_readiness(self):
        """GET /ready — readiness probe."""
        self.client.get("/ready", name="/ready")

    @task(1)
    def check_metrics(self):
        """GET /metrics — Prometheus metrics."""
        self.client.get("/metrics", name="/metrics")


class ChatUser(MeridianAPIUser):
    """Load test for the RAG chat pipeline."""

    weight = 5

    SAMPLE_QUESTIONS = [
        "How much did I spend on food last month?",
        "What is my current budget status?",
        "Can you analyze my subscription spending?",
        "What are my top 5 spending categories?",
        "How does my spending this month compare to last month?",
        "What is the 50/30/20 budgeting rule?",
        "Should I increase my emergency fund?",
        "What are some ways to reduce my grocery spending?",
        "How much am I spending on transportation?",
        "What is my average monthly utility bill?",
    ]

    @task(10)
    def send_chat_message(self):
        """POST /v1/chat — non-streaming chat."""
        question = random.choice(self.SAMPLE_QUESTIONS)
        payload = {
            "message": question,
            "stream": False,
        }
        with self.client.post(
            "/v1/chat",
            json=payload,
            headers=self.auth_headers,
            name="/v1/chat",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify response structure
                if "content" not in data:
                    response.failure("Missing 'content' in response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            elif response.status_code == 429:
                response.failure("Rate limited")

    @task(3)
    def send_chat_with_conversation(self):
        """POST /v1/chat — continue an existing conversation."""
        conversation_id = str(uuid.uuid4())
        payload = {
            "message": "Tell me more about my spending habits.",
            "conversation_id": conversation_id,
            "stream": False,
        }
        self.client.post(
            "/v1/chat",
            json=payload,
            headers=self.auth_headers,
            name="/v1/chat [conversation]",
        )


class DocumentIngestionUser(MeridianAPIUser):
    """Load test for document ingestion."""

    weight = 1

    SAMPLE_DOCUMENTS = [
        {
            "content": "The 50/30/20 rule is a budgeting guideline that suggests allocating "
                       "50% of after-tax income to needs, 30% to wants, and 20% to savings "
                       "and debt repayment. This approach provides a simple framework for "
                       "managing personal finances without detailed tracking of every expense.",
            "content_type": "advice",
            "filename": "budgeting_guide.txt",
        },
        {
            "content": "Emergency funds should typically cover 3-6 months of essential living "
                       "expenses. Keep emergency savings in a high-yield savings account for "
                       "easy access while earning interest. Start small with a goal of $1,000 "
                       "and gradually build up to the full amount.",
            "content_type": "advice",
            "filename": "emergency_fund_guide.txt",
        },
    ]

    @task
    def ingest_document(self):
        """POST /v1/documents — ingest a sample document."""
        doc = random.choice(self.SAMPLE_DOCUMENTS)
        self.client.post(
            "/v1/documents",
            json=doc,
            headers=self.api_key_headers,
            name="/v1/documents",
        )

    @task
    def check_stats(self):
        """GET /v1/documents/stats — check knowledge base stats."""
        self.client.get(
            "/v1/documents/stats",
            headers=self.api_key_headers,
            name="/v1/documents/stats",
        )
