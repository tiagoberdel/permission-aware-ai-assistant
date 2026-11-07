# Andino — Secure Permission-Aware AI Assistant

Andino is a backend project for an internal AI assistant designed to answer questions about company documents while respecting role-based access control (RBAC).

The main goal is to ensure that users can only retrieve information from documents they are authorized to access. Access control must be enforced by the backend, before retrieved content reaches the language model.

## Project Goals

- Build an authenticated API for an internal assistant.
- Model users, roles, and document permissions.
- Enforce document-level access control on the server side.
- Integrate document retrieval with an AI agent.
- Evaluate the system against unauthorized access attempts, prompt injection, and information leakage.

## Planned Architecture

The planned architecture consists of:

- **FastAPI:** API and application layer.
- **PostgreSQL:** Persistent storage for users, roles, and audit logs.
- **SQLAlchemy and Alembic:** ORM and database migrations.
- **Chroma:** Vector storage for document retrieval.
- **FastMCP:** MCP server exposing retrieval capabilities.
- **LangChain:** Agent orchestration and tool integration.
- **Pytest:** Automated tests and security evaluation.
- **Langfuse:** Planned tracing and observability.

The retrieval layer will apply permission filters server-side. The language model will not be responsible for deciding whether a user is authorized to access a document.

## Access Control Model

Andino uses four predefined roles:

| Role | Description |
|---|---|
| `employee` | General employee access |
| `sales` | Sales department access |
| `finance` | Finance department access |
| `hr` | Human Resources access |

- Every internal user has the `employee` role.
- Internal users may have multiple roles.
- The general manager has all four roles.
- The external Visitor identity has no internal roles and is explicitly identified as a visitor.

A document is accessible when the user's roles intersect with the document's `allowed_roles`.

Documents will also have a sensitivity label:

- `public`
- `internal`
- `confidential`

Sensitivity labels provide additional document metadata; they do not replace the role-based access check.

## Security Principles

- Identity is obtained from the authenticated backend session, never from user prompts or model-generated arguments.
- Authorization is enforced before document content is passed to the language model.
- Unauthorized documents must not reach the model.
- Responses to inaccessible information should not reveal whether a document exists or whether access was denied.
- Requests and retrieval decisions will be recorded for auditing.

## Demo Dataset

The planned demonstration dataset consists of:

- 40 AI-generated documents in Spanish.
- 6 internal demo users.
- 1 external Visitor identity.
- 4 predefined roles.
- A ground-truth access matrix describing which users can access each document.
- Unique canary facts in documents to help detect unauthorized information disclosure.

The demo identities will represent different organizational roles and permission combinations.

## Evaluation Plan

The evaluation suite is intended to measure both answer quality and access-control security.

Planned evaluation data:

- 30 questions with expected outcomes:
  - 14 answerable questions.
  - 16 questions that should not produce an answer from the available authorized documents.
- 10 attack scenarios covering 8 categories:
  - Direct requests.
  - Role impersonation.
  - Authority claims.
  - Instruction overrides.
  - Indirect prompt injection.
  - Obfuscation.
  - Inference by aggregation.
  - Document existence probing.

Planned metrics:

- **Leak rate:** unauthorized information disclosed.
- **False refusal rate:** valid questions refused despite accessible information.
- **Answer accuracy:** correctness of answers against expected results.
- **Existence-leak rate:** cases where the system reveals information about inaccessible documents.
- **Latency:** response time.
- **Cost:** estimated cost per query.

Evaluation results will be reported from actual test runs, not assumed or hardcoded.

## Current Implementation

The project is currently in its backend foundation stage.

Implemented:

- FastAPI application setup.
- PostgreSQL connection.
- SQLAlchemy models for users, roles, and user-role relationships.
- Alembic database migrations.
- Password hashing and verification.
- JWT access-token creation and validation.
- Authentication dependencies for retrieving the current user.
- Login endpoint.
- Demo role and user seeding, including the Visitor identity.
- Automated tests for authentication, models, and related components.

Document ingestion, vector retrieval, permission-aware search, MCP integration, agent orchestration, and the evaluation pipeline are still pending.

## Roadmap

1. **Backend foundation:** database models, migrations, authentication, and demo identities.
2. **Document ingestion:** generate the demo corpus, split documents into chunks, and attach permission metadata.
3. **Permission-aware retrieval:** implement server-side filtering and test access against the ground-truth matrix.
4. **MCP integration:** expose retrieval through an MCP tool while preserving authenticated identity.
5. **Agent orchestration:** integrate the retrieval tool into an AI assistant.
6. **Security evaluation:** run the question set and attack scenarios, measure leakage and answer quality.
7. **Observability and deployment:** add tracing, evaluate performance, and deploy a reproducible demo.

---

**Project status:** Backend foundation in progress.