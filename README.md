# Secure Permission-Aware AI Assistant

An end-to-end AI engineering project: an internal assistant that answers questions over company documents while enforcing role-based access control (RBAC), tested against leaks and prompt-injection attacks.

## Problem

Internal AI assistants can leak documents that a user is not allowed to see, even when they are tricked into it. Here, permissions are enforced in the server layer, not in the prompt: a document the user cannot access never reaches the model.

## Data

All data is synthetic: an AI-generated set of 40 documents from a fictional company (written in Spanish), with 6 test users, canary facts, and ground-truth access rules. See [`data/`](data/).

## Stack

**V1**
- FastAPI: API and authentication
- PostgreSQL: users and audit log
- Chroma: vector store with metadata filters
- FastMCP: tool server that exposes retrieval to the agent
- LangChain: agent loop
- pytest: access and security tests
- Docker: everything runs in containers

**Planned:** Langfuse (tracing and evaluation), cloud deployment.

## Access model

- Every authenticated user has the `employee` role. Other roles: `sales`, `finance`, `hr`. A user can hold several roles (the general manager holds all of them).
- A user can see a document if they share at least one role with its `allowed_roles`.
- Sensitivity levels: `public`, `internal`, `confidential`.

| Document | Level | Employee | Sales | Finance | HR |
|---|---|---|---|---|---|
| Annual leave policy | public | ✓ | ✓ | ✓ | ✓ |
| Rate card | internal | - | ✓ | - | - |
| Commission plan | confidential | - | ✓ | - | - |
| Margin by business line | confidential | - | - | ✓ | - |
| Salary scale | confidential | - | - | - | ✓ |
| Sales quotas and commercial budget | confidential | - | ✓ | ✓ | - |
| 2027 salary adjustment plan | confidential | - | - | ✓ | ✓ |

## Security design

- Identity comes from the authenticated session, never from the prompt or from arguments the model fills in.
- The retrieval filter is applied server-side, before anything reaches the model.
- When access is denied, the assistant answers "I couldn't find information about that", so it does not confirm that a document exists.
- Every request is written to an audit log: who asked what, which documents were retrieved, and the decision.

## Evaluation

- **Canary facts:** every document contains a unique fake fact. If it appears in a response to an unauthorized user, that is a leak.
- **Questions:** 30 questions with expected behavior (14 the user may answer, 16 they may not).
- **Attacks:** 10 attacks across these categories: direct request, role impersonation, authority claim, instruction override, indirect prompt injection (instructions hidden inside documents), obfuscation, inference by aggregation, and existence probing.
- **Ground truth:** a document × user access matrix.

Metrics: leak rate, false refusals, answer accuracy, existence-leak rate, cost and latency per query.

Results: _to be added once measured._

## Roadmap

- [ ] 1. Ingestion: chunking and metadata
- [ ] 2. Login and permission-filtered search, validated by the access-matrix test
- [ ] 3. MCP server exposing retrieval with the session identity
- [ ] 4. Agent that uses the MCP tools
- [ ] 5. Attack suite, evaluation and defense comparison
- [ ] 6. Observability, deployment and write-up

## Run it

_Coming soon._