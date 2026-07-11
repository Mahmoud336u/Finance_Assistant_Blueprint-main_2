# ADR-001: Core Technology Stack Selection

**Status:** Accepted
**Date:** 2026-07-01
**Author:** Mahmoud Heshmat

## Context

We need to select the core technology stack for Meridian, an enterprise multi-region RAG platform for financial intelligence. The system must support:
- High-throughput transaction processing
- AI-powered chat with RAG (Retrieval-Augmented Generation)
- Multi-region deployment with sub-second failover
- Bank-grade security and compliance (GDPR, PCI-DSS scope reduction, SOC2)

## Decision

### Backend: Python 3.12 + FastAPI
- **Why:** Async-first, Pydantic validation, automatic OpenAPI spec, Python AI/ML ecosystem alignment
- **Alternatives rejected:** Go (stronger performance, but weaker AI/ML ecosystem), Node.js (weaker type safety, less mature async DB libraries)

### Database: Aurora PostgreSQL 15 + pgvector
- **Why:** ACID compliance for financial data, pgvector colocation avoids extra infrastructure, Aurora Global Database for DR
- **Alternatives rejected:** Separate Pinecone (additional cost and ops at < 50M vectors), MongoDB (weaker ACID for financial transactions)

### AI/LLM: AWS Bedrock (Claude) + Azure OpenAI (fallback)
- **Why:** Bedrock PrivateLink prevents data egress, unified AWS billing, multi-provider redundancy
- **Alternatives rejected:** Direct Anthropic API (no PrivateLink, data leaves VPC), single provider (single point of failure)

### IaC: Terraform
- **Why:** Multi-region support, explicit state management, large community, cloud-agnostic potential
- **Alternatives rejected:** CDK (too magical, harder to reason about state), Pulumi (smaller community for AWS)

### Container orchestration: ECS Fargate
- **Why:** No node management, per-second billing, simpler ops than Kubernetes
- **Alternatives rejected:** EKS (operational complexity not justified at current scale)

### Cache: ElastiCache Redis 7
- **Why:** Sub-millisecond latency, Lua scripting for atomic ops, Global Datastore for DR
- **Alternatives rejected:** Memcached (no persistence, no data structures), DynamoDB DAX (Aurora not DynamoDB)

## Consequences

- Python performance ceiling exists for CPU-bound work — mitigated by offloading to managed services (Bedrock, SageMaker)
- ECS Fargate has no GPU support for large models — use EC2 for vLLM self-hosted inference
- Terraform requires manual state management — mitigated by remote state in S3 + DynamoDB lock
- pgvector at > 50M vectors may require migration to Pinecone — documented as a known scaling boundary
