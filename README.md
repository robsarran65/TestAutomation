# AI-Powered Test Automation SaaS Platform

A production-ready AI-powered testing platform for validating web applications and API microservices. The project combines a multi-agent coordination layer, AI-assisted test generation, browser automation, and structured reporting into a platform suitable for QA teams, engineering teams, and software delivery organizations.

## Product vision

This solution is designed to help businesses reduce manual QA effort, speed up release cycles, and improve confidence in web and API changes. It provides:

- AI-assisted test generation from natural-language requirements
- Web UI validation using browser automation
- API validation for microservice flows and contract checks
- Multi-agent orchestration for parallel execution and result aggregation
- Executive-quality HTML and PDF reporting
- Cloud deployment for SaaS and enterprise usage

## Why this is valuable as a SaaS product

Businesses want a product that can:

- execute regression suites across web apps and APIs
- generate tests automatically from user stories or defects
- reduce manual effort for repetitive QA tasks
- support multiple teams, projects, and environments
- provide visible reporting for product, QA, and engineering stakeholders

This project is a strong foundation for a SaaS product because it already includes: 

- a coordinator/worker orchestration model
- specialized agents for execution, validation, generation, and reporting
- a dashboard-oriented UI via Streamlit
- report generation artifacts and execution examples

## Core capabilities

### Web application testing
- browser-based test execution
- login and form validation scenarios
- UI element interaction and verification
- flow-based regression testing

### API microservice testing
- GET/POST/PUT/DELETE validation
- response schema and status validation
- JSON field verification
- contract and payload validation

### AI-assisted testing
- natural language test generation
- reusable data generation for test scenarios
- failure analysis suggestions
- optimization recommendations for large suites

### Reporting and insight
- HTML reports
- summary metrics and pass/fail rates
- visual execution analytics
- report artifact storage for stakeholders

## Architecture overview

```text
Browser / API clients
        |
        v
Streamlit SaaS UI / Dashboard
        |
        v
Coordinator Agent (manager)
        |
        +--> Test Executor Agent
        +--> AI Generation Agent
        +--> Report Agent
        +--> Locator Repair Agent
        +--> Data Validation Agent
        +--> Performance Analyzer Agent
        |
        v
Execution workers + storage + report output
```

## Repository structure

Standard Python src-layout — the importable package lives under `src/`.

- `src/ai_test_engine/` — the package
  - `app.py` / `app_multiagent.py` — Streamlit dashboards (single- and multi-agent)
  - `agents/` — coordinator, executor, AI generation, reporting, specialized agents
  - `core/` — keyword engine, test runner, browser factory, AI helpers
  - `config/settings.py` — all paths and environment-backed settings
  - `prompts.py` — LLM prompt templates
- `tests/` — pytest suite (104 tests, no browser or network required)
- `data/test_data/` — sample `.xlsx` test workbooks
- `outputs/` — generated reports, logs, screenshots (git-ignored)
- `docs/` — architecture, deployment, quickstart
- `scripts/` — standalone utilities

Full detail: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

## Local quick start

Requires **Python 3.9+** and **Google Chrome** (UI tests drive a real browser).

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
```

### 2. Install

```bash
pip install -e ".[dev]"
```

Installs the package plus pytest. `pip install -r requirements.txt` gets
runtime dependencies only.

### 3. Configure (optional)

```bash
cp .env.example .env
```

Runs fully offline with no `.env` — `AI_PROVIDER` defaults to `stub`.

### 4. Verify the install

```bash
pytest
```

### 5. Run the dashboard

```bash
streamlit run src/ai_test_engine/app_multiagent.py
```

or the installed console script:

```bash
ai-test-engine
```

Upload any workbook from `data/test_data/` and run it. Reports are written to
`outputs/reports/`.

### 6. Optional: run the demo workflow

```bash
python -m ai_test_engine.demo_workflow
```

Exercises all five agents end to end. Drives a real browser — set
`HEADLESS=true` to run without a visible window.

## Configuration

All settings are environment variables, read at import by
`config/settings.py`. See `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `stub` | `stub` (offline), `openai`, or `claude` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | — | Required only for the matching provider |
| `HEADLESS` | `true` outside development | Run Chrome with no window. **Required on servers, containers and CI.** |
| `DEFAULT_TIMEOUT` | `10` | Seconds Selenium retries a locator before failing a step |
| `PAGE_LOAD_TIMEOUT` | `60` | Seconds to wait for a page load |
| `API_TIMEOUT` | `30` | Seconds before an API step gives up |
| `VERIFY_SSL` | `true` | Set false only for a client with an internal CA |
| `WINDOW_WIDTH` / `WINDOW_HEIGHT` | `1920` / `1080` | Browser viewport |
| `SCREENSHOT_ON_FAILURE` | `true` | Capture screenshots into `outputs/screenshots/` |
| `AI_TEST_ENGINE_HOME` | auto-detected | Where `outputs/` and `data/` live. Set this when running from an installed package. |

Report and log locations are **not** configurable — they are always
`outputs/{reports,logs,screenshots}`.

## SaaS deployment model

This project is suitable for a SaaS or managed enterprise deployment using a multi-tenant architecture. The recommended model is:

- one shared web app for users and admins
- one central coordinator layer for tasks and workloads
- worker services that execute browser and API tests
- a database for tenants, projects, runs, and reporting metadata
- object storage for artifacts, screenshots, logs, and exported reports
- secret management for API keys and environment settings

### Recommended cloud architecture

#### Microsoft Azure
- Azure Container Apps or Azure App Service for the UI
- Azure Container Apps / Azure Functions for worker jobs
- Azure Database for PostgreSQL or Azure SQL
- Azure Blob Storage for reports and screenshots
- Azure Key Vault for secrets
- Azure Monitor / Log Analytics for observability

#### AWS
- ECS or EKS for app and workers
- RDS for persistent data
- S3 for storage
- Secrets Manager
- CloudWatch for metrics and alerting

## Production SaaS deployment pattern

```text
Users (QA teams / developers / admins)
            |
            v
[Web App / Streamlit SaaS UI]
            |
            v
[API / orchestration layer]
            |
            +--> [Background workers]
            |       - web execution
            |       - API execution
            |       - report generation
            |
            +--> [PostgreSQL / database]
            |
            +--> [Queue / Redis]
            |
            +--> [Object storage: logs, reports, screenshots]
```

## Deployment steps for SaaS

### 1. Prepare environment configuration

Use `.env.example` as the starting point and set real production values:

```env
APP_ENV=production
APP_PORT=8501
SECRET_KEY=replace-with-secure-secret
DATABASE_URL=postgresql://user:password@host:5432/ai_test_engine
REDIS_URL=redis://host:6379/0
REPORT_STORAGE_PATH=/mnt/reports
LOG_LEVEL=INFO
AI_PROVIDER=stub
OPENAI_API_KEY=
```

### 2. Containerize the application

Use the included Dockerfile:

```bash
docker build -t ai-test-engine:latest .
```

### 3. Deploy the app to a managed cloud service

Example Azure deployment pattern:

```bash
az acr build --registry myregistry --image ai-test-engine:latest .
```

Then deploy to Azure Container Apps or App Service with the proper environment variables and secret bindings.

### 4. Run background workers separately

Use the same codebase, but deploy workers that run queue-based jobs for:

- web UI execution
- API checks
- report generation
- queue retry and status updates

### 5. Set up persistent data and storage

Required services:

- database for users, projects, runs, and reports
- object storage for screenshots and artifacts
- queue service to handle asynchronous tasks
- monitoring for failed jobs, queue depth, and app health

### 6. Enable multi-tenancy and security

For a SaaS deployment, add:

- tenant separation for projects and data
- role-based access control
- secure login / admin access
- secrets management
- audit logs for all runs and exports

## Operational requirements for SaaS launch

Before selling this product, the business should include:

- secure authentication and authorization
- project dashboards for QA and engineering teams
- scheduled execution jobs
- notification integrations (email, Slack, webhooks)
- alerting for failed runs and queue backlog
- compliance-friendly audit trails
- support for CI/CD integrations

## Security and governance

This product should be deployed with a security-first design:

- secrets stored in a secret manager, not in code
- least-privilege access for infrastructure
- HTTPS-only production deployments
- tenant-scoped isolation for customer data
- validation for uploaded payloads and generated prompts
- audit records for report download and test execution actions

See [SECURITY.md](SECURITY.md) for the security policy.

## GitHub and release readiness

This repo is structured for GitHub publishing and CI-based validation.

- CI workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- GitHub publishing guide: [GITHUB_PUSH_GUIDE.md](GITHUB_PUSH_GUIDE.md)
- release checklist: [REPO_RELEASE_CHECKLIST.md](REPO_RELEASE_CHECKLIST.md)

## Roadmap to SaaS commercialization

### Phase 1 — MVP foundation
- secure configuration and secret management
- queue-based execution workers
- persistent storage for jobs and reports
- multi-project dashboard and reporting

### Phase 2 — Business-ready platform
- user management and RBAC
- tenant separation
- scheduled executions and notifications
- SaaS billing and admin controls

### Phase 3 — Enterprise scale
- SSO and enterprise security
- vertical expansion for API contract testing
- large-scale parallel execution
- advanced AI repair and optimization workflows

## Recommended business model

A sensible commercial model for this product is:

- free tier for individual users or small teams
- paid tier for teams with more test execution volume
- enterprise plan with RBAC, SSO, reporting, and SLA support
- premium AI add-on for test generation and optimization features

## Quick reference for deployment to cloud

```bash
# build locally
Docker build -t ai-test-engine:latest .

# run locally with docker-compose
Docker compose up --build

# deploy to Azure Container Apps or App Service
# set environment variables and secret references in the cloud console or CLI
```

## License

This codebase is a starter platform intended for business evaluation and productionization. You should review licensing and commercial terms before selling it as a hosted service or enterprise product.

## Summary

This project is already a strong foundation for a commercial AI testing platform. The next step is to treat it as a SaaS product: add tenant-aware architecture, robust cloud deployment, secure operations, and a clean GitHub release process. The repository already includes the structure needed to begin that migration.
