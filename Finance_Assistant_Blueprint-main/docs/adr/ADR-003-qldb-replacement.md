# ADR-003: Replace QLDB with DynamoDB Streams + S3 Object Lock for Audit Ledger

**Status:** Accepted
**Date:** 2026-07-01
**Author:** Mahmoud Heshmat

## Context

The original system blueprint (Section 5.4, 6.2) specified Amazon QLDB as the immutable audit ledger for tracking all financial data mutations. QLDB provides a cryptographically verifiable, append-only journal — ideal for an audit trail.

However, **Amazon QLDB was deprecated for new customers as of July 31, 2024**. Existing customers have until July 31, 2025 to complete migration. Since this project starts in July 2026, QLDB is not available.

## Decision

Replace QLDB with a combination of:

1. **DynamoDB Streams** — capture all mutations as a stream of events
2. **Lambda** — process stream events, compute hash chains, and write to S3
3. **S3 with Object Lock (Compliance Mode)** — immutable, tamper-evident storage
4. **Hash chaining** — each audit record includes SHA-256 hash of the previous record, creating a verifiable chain

### Audit Record Schema (DynamoDB → S3)

```json
{
  "audit_id": "aud_01J9XK2MNPQR4T8V",
  "timestamp": "2026-07-01T14:23:11.842Z",
  "entity_type": "transaction",
  "entity_id": "txn_01J9XK2MNPQR4T8W",
  "action": "create",
  "actor_id": "usr_01J9ABC",
  "actor_type": "user",
  "before": null,
  "after": { "...": "..." },
  "previous_hash": "a1b2c3d4...",
  "record_hash": "e5f6g7h8...",
  "metadata": {
    "source_service": "transaction-service",
    "correlation_id": "req_01J9XK2"
  }
}
```

### Hash Chain Verification

```python
def verify_chain(records: list[AuditRecord]) -> bool:
    for i, record in enumerate(records):
        expected_hash = sha256(json.dumps(record.without_hash(), sort_keys=True))
        if record.record_hash != expected_hash:
            return False
        if i > 0 and record.previous_hash != records[i-1].record_hash:
            return False
    return True
```

## Alternatives Considered

| Alternative | Why Rejected |
|---|---|
| **Amazon Timestream** | Not designed for audit ledger; no hash chain support; analytics-oriented |
| **Managed blockchain (Hyperledger)** | Massive operational complexity; overkill for single-org audit trail |
| **PostgreSQL with append-only table** | Possible to alter with admin access; not truly immutable; no Object Lock |
| **Custom KV store with WAL** | Build vs. buy; S3 Object Lock provides stronger immutability guarantee |

## Consequences

- **Pro:** No dependency on deprecated service. S3 Object Lock provides regulatory-grade immutability.
- **Pro:** Hash chaining provides independent verifiability without needing a managed ledger.
- **Pro:** Significantly cheaper than QLDB at scale (S3 storage vs. QLDB IO pricing).
- **Con:** Hash chain verification is application-level, not built into the storage layer.
- **Con:** DynamoDB Streams has a 24-hour retention; Lambda must process promptly or events are lost.
- **Mitigation:** CloudWatch alarm on DynamoDB Streams iterator age; DLQ for failed Lambda invocations.
