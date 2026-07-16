# Meridian GitHub Project Board Implementation

This document implements the GitHub Project board setup defined in the delivery plan README.

## 1) Board structure

### Columns
- **Backlog**
- **In Progress**
- **Done**

### Tracks (Phase grouping)
- **Phase 1 (MVP)**
- **Phase 2 (Production)**
- **Phase 3 (Enterprise)**
- **Phase 4 (Global/Stretch)**

### Required fields
- **Sprint** (number or range, e.g., `1`, `7–8`)
- **Phase** (`Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`)
- **Owner** (default: `Mahmoud Heshmat`)
- **Target Date** (YYYY-MM-DD)
- **Exit Criteria** (short acceptance statement)

## 2) Timeline and phase assignment

| Phase | Sprint range | Timeline | Scope |
|---|---:|---|---|
| Phase 1 (MVP) | 1–6 | Jul 2026 → Sep 2026 | Foundation + IaC, Data + Core RAG, Auth/CI + MVP deploy/demo |
| Phase 2 (Production) | 7–16 | Oct 2026 → Feb 2027 | Security, orchestration/routing, observability, semantic cache, load/SLO + blue-green |
| Phase 3 (Enterprise) | 17–28 | Mar 2027 → Aug 2027 | DataOps ingestion, HITL governance, fraud/SSO/audit |
| Phase 4 (Global/Stretch) | 29–36 | Sep 2027 → Dec 2027 | Multi-region deployment, replication, failover drills |

## 3) Milestones

| Milestone | Target date |
|---|---|
| **M0 — Kickoff** | 2026-07-01 |
| **M1 — MVP demo** | 2026-09-30 |
| **M2 — Production launch** | 2027-02-28 |
| **M3 — Enterprise-ready** | 2027-08-31 |
| **M4 — Global DR validated** | 2027-12-31 |

### Milestone acceptance checks (copied from definition of done)

#### M1 — MVP demo (Phase 1 done)
- [ ] Terraform modules for vpc/ecs/aurora/redis apply in a fresh AWS account
- [ ] `/v1/chat` returns grounded cited responses for at least 20 queries
- [ ] CI runs lint + unit tests + Docker build on every PR
- [ ] Cognito-protected endpoints reject unauthenticated requests
- [ ] Fresh clone finishes README getting-started in < 30 minutes
- [ ] Demo video recorded and linked from README

#### M2 — Production launch (Phase 2 done)
- [ ] Prompt-injection test set blocked at >= 90% by WAF + validator
- [ ] p99 latency < 2s at target load with archived load report
- [ ] Dashboard shows latency, cache hit rate, cost, and RAGAS faithfulness
- [ ] At least one zero-downtime blue-green deployment to staging
- [ ] Semantic cache hit rate >= 15% on benchmark query set

#### M3 — Enterprise-ready (Phase 3 done)
- [ ] External source ingested continuously via Kinesis for >= 7 days
- [ ] >= 50 HITL reviews completed and logged
- [ ] Audit ledger entries are hash-chained and independently verifiable
- [ ] PII redaction verified against synthetic PII test corpus

#### M4 — Global DR validated (Phase 4 done)
- [ ] `eu-central-1` stack deploys from same modules as `us-east-1`
- [ ] >= 2 failover drills documented with measured RTO/RPO
- [ ] DR runbook published in `docs/runbooks/`

## 4) Current assignment

| Item | Sprint | Phase | Status | Target Date | Dependency |
|---|---:|---|---|---|---|
| Sprint 1: Project foundation | 1 | Phase 1 | **In Progress** | 2026-07-14 | — |
| Sprint 2: Data layer | 2 | Phase 1 | **Backlog** | 2026-07-28 | Blocked until Sprint 1 exit criteria are met |

## 5) Governance cadence

- Sprint length: **2 weeks**
- Buffer policy: **1-week buffer after every 3 sprints**
- Recurring sprint tasks:
  - Update `CHANGELOG.md`
  - Add sprint planning note under `docs/sprints/`
  - Add sprint retro note under `docs/sprints/`

Use `docs/sprints/recurring-sprint-checklist.md` as the standard recurring checklist each sprint.
