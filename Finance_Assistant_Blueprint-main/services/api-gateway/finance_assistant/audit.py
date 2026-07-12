"""Meridian — Audit Trail Service.

Implements an append-only audit log per ADR-003 (QLDB Replacement).
Uses DynamoDB for the event log and S3 with Object Lock for
tamper-proof long-term archival.

In development, falls back to local JSON logging when DynamoDB
is unavailable.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum

import boto3

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)

_dynamo_client = None
_s3_client = None


class AuditAction(str, Enum):
    """Types of auditable actions."""

    # Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_MFA_ENABLE = "user.mfa_enable"
    USER_DEACTIVATE = "user.deactivate"

    # Transactions
    TRANSACTION_CREATE = "transaction.create"
    TRANSACTION_UPDATE = "transaction.update"
    TRANSACTION_CATEGORIZE = "transaction.categorize"

    # Accounts
    ACCOUNT_LINK = "account.link"
    ACCOUNT_UNLINK = "account.unlink"
    ACCOUNT_SYNC = "account.sync"

    # Budgets
    BUDGET_CREATE = "budget.create"
    BUDGET_UPDATE = "budget.update"
    BUDGET_DELETE = "budget.delete"
    BUDGET_ALERT = "budget.alert"

    # AI
    AI_CHAT = "ai.chat"
    AI_DOCUMENT_INGEST = "ai.document_ingest"
    AI_ANOMALY_DETECT = "ai.anomaly_detect"

    # Security
    GUARDRAIL_BLOCK = "security.guardrail_block"
    RATE_LIMIT_HIT = "security.rate_limit"
    AUTH_FAILURE = "security.auth_failure"

    # Admin
    ADMIN_DATA_EXPORT = "admin.data_export"
    ADMIN_DATA_DELETE = "admin.data_delete"


def _get_dynamo_client():
    """Get or create DynamoDB client."""
    global _dynamo_client
    if _dynamo_client is None:
        settings = get_settings()
        _dynamo_client = boto3.client("dynamodb", region_name=settings.aws_region)
    return _dynamo_client


def _get_s3_client():
    """Get or create S3 client."""
    global _s3_client
    if _s3_client is None:
        settings = get_settings()
        _s3_client = boto3.client("s3", region_name=settings.aws_region)
    return _s3_client


async def record_audit_event(
    action: AuditAction,
    *,
    user_id: str | None = None,
    resource_id: str | None = None,
    resource_type: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> str:
    """Record an auditable event to the immutable audit trail.

    Events are written to:
    1. DynamoDB (for querying and real-time access)
    2. S3 with Object Lock (for tamper-proof archival)

    Args:
        action: The type of auditable action.
        user_id: The ID of the user who performed the action.
        resource_id: The ID of the resource acted upon.
        resource_type: The type of resource (e.g., "transaction", "account").
        details: Additional context about the action.
        ip_address: The client IP address.
        request_id: The request correlation ID.

    Returns:
        The audit event ID.
    """
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    event = {
        "event_id": event_id,
        "timestamp": timestamp,
        "action": action.value,
        "user_id": user_id,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "details": details or {},
        "ip_address": ip_address,
        "request_id": request_id,
    }

    # Try DynamoDB first
    try:
        await _write_to_dynamo(event)
    except Exception as exc:
        # Fall back to structured logging
        await logger.awarning(
            "DynamoDB audit write failed, logging locally",
            error=str(exc),
        )
        await logger.ainfo("audit_event", **event)

    # Async S3 archival (fire-and-forget in production; would use SQS/SNS)
    try:
        await _write_to_s3(event)
    except Exception as exc:
        await logger.awarning("S3 audit archival failed", error=str(exc))

    return event_id


async def _write_to_dynamo(event: dict) -> None:
    """Write an audit event to DynamoDB.

    Table: {project_name}-{env}-audit-events
    Partition key: user_id (or "system" for non-user events)
    Sort key: timestamp#event_id
    """
    settings = get_settings()
    table_name = f"{settings.app_name}-{settings.environment}-audit-events"

    partition_key = event.get("user_id") or "system"
    sort_key = f"{event['timestamp']}#{event['event_id']}"

    client = _get_dynamo_client()
    client.put_item(
        TableName=table_name,
        Item={
            "pk": {"S": partition_key},
            "sk": {"S": sort_key},
            "event_id": {"S": event["event_id"]},
            "timestamp": {"S": event["timestamp"]},
            "action": {"S": event["action"]},
            "user_id": {"S": event.get("user_id") or ""},
            "resource_id": {"S": event.get("resource_id") or ""},
            "resource_type": {"S": event.get("resource_type") or ""},
            "details": {"S": json.dumps(event.get("details", {}))},
            "ip_address": {"S": event.get("ip_address") or ""},
            "request_id": {"S": event.get("request_id") or ""},
        },
    )


async def _write_to_s3(event: dict) -> None:
    """Archive an audit event to S3 with Object Lock.

    Bucket: {project_name}-{env}-audit-archive
    Key: audit/{YYYY}/{MM}/{DD}/{event_id}.json

    Object Lock ensures events cannot be deleted or overwritten
    for the retention period (per ADR-003).
    """
    settings = get_settings()
    bucket_name = f"{settings.app_name}-{settings.environment}-audit-archive"
    dt = datetime.fromisoformat(event["timestamp"])
    key = f"audit/{dt.year}/{dt.month:02d}/{dt.day:02d}/{event['event_id']}.json"

    client = _get_s3_client()
    client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(event, default=str),
        ContentType="application/json",
    )


async def query_audit_trail(
    user_id: str,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    action_filter: AuditAction | None = None,
    limit: int = 50,
) -> list[dict]:
    """Query the audit trail for a specific user.

    Args:
        user_id: The user whose audit trail to query.
        start_time: ISO format start time.
        end_time: ISO format end time.
        action_filter: Optional filter by action type.
        limit: Maximum number of events to return.

    Returns:
        List of audit events, most recent first.
    """
    settings = get_settings()
    table_name = f"{settings.app_name}-{settings.environment}-audit-events"

    try:
        client = _get_dynamo_client()

        key_condition = "pk = :pk"
        expression_values: dict = {":pk": {"S": user_id}}

        if start_time and end_time:
            key_condition += " AND sk BETWEEN :start AND :end"
            expression_values[":start"] = {"S": start_time}
            expression_values[":end"] = {"S": end_time}

        params: dict = {
            "TableName": table_name,
            "KeyConditionExpression": key_condition,
            "ExpressionAttributeValues": expression_values,
            "ScanIndexForward": False,  # Most recent first
            "Limit": limit,
        }

        if action_filter:
            params["FilterExpression"] = "action = :action"
            expression_values[":action"] = {"S": action_filter.value}

        response = client.query(**params)
        items = response.get("Items", [])

        return [
            {
                "event_id": item["event_id"]["S"],
                "timestamp": item["timestamp"]["S"],
                "action": item["action"]["S"],
                "resource_id": item.get("resource_id", {}).get("S"),
                "resource_type": item.get("resource_type", {}).get("S"),
                "details": json.loads(item.get("details", {}).get("S", "{}")),
            }
            for item in items
        ]

    except Exception as exc:
        await logger.aerror("Audit trail query failed", error=str(exc))
        return []
