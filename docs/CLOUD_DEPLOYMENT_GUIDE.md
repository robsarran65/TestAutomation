# Cloud Deployment Guide

## Overview

This guide explains how to deploy the AI-powered test automation platform to the cloud for business use. The system is designed for web application testing, API microservice validation, and AI-assisted test generation. It can be deployed as a hosted SaaS, internal enterprise platform, or a managed product environment.

## Recommended architecture

For a production business deployment, use a containerized architecture with the following components:

- Frontend / dashboard: Streamlit app
- Workload orchestration: coordinator and worker services
- Background execution workers: asynchronous task processing
- Database: PostgreSQL or Azure SQL for metadata and test execution state
- Cache / queue: Redis or managed queue service
- Storage: Azure Blob Storage or S3 for test artifacts and reports
- Monitoring: application logs, metrics, uptime checks, alerts
- Secrets management: Azure Key Vault or AWS Secrets Manager

## Recommended cloud stack

### Option A: Microsoft Azure (recommended for this stack)

- App Service or Azure Container Apps for the Streamlit web app
- Azure Container Apps or Azure Functions for background workers
- Azure Database for PostgreSQL or Azure SQL
- Azure Blob Storage for reports and logs
- Azure Key Vault for secrets
- Azure Monitor + Log Analytics for observability
- Azure Container Registry for images

### Option B: AWS

- ECS / EKS / EC2 for container hosting
- RDS for database
- S3 for reports and artifacts
- Secrets Manager
- CloudWatch + ALB / Route53

## Production architecture diagram

```text
User / Browser
      |
      v
[Streamlit UI / Dashboard]
      |
      v
[Coordinator API / Orchestration Layer]
      |\
      | \__ schedules tasks / workflow execution
      v
[Worker Services]
  - Web test execution
  - API validation
  - AI generation
  - Reporting
      |
      v
[PostgreSQL / SQL Database]
      |
      +--> [Blob Storage for artifacts and reports]
      |
      +--> [Redis / Queue]
      |
      +--> [Monitoring / Alerts]
```

## Prerequisites

Before deployment, prepare the following:

- A cloud subscription with administrative access
- Container registry access
- Database service and credentials
- Storage account for generated artifacts
- Secrets management service
- DNS and HTTPS configuration
- CI/CD pipeline or deployment automation

## Deployment steps

### 1. Prepare environment variables

Create a production environment file with values such as:

```env
APP_ENV=production
APP_PORT=8501
SECRET_KEY=replace-with-secure-secret
DATABASE_URL=postgresql://user:password@host:5432/appdb
REDIS_URL=redis://host:6379/0
REPORT_STORAGE_PATH=/mnt/reports
LOG_LEVEL=INFO
OPENAI_API_KEY=
AI_PROVIDER=stub
```

Do not commit real secrets to source control. Use a secrets manager or CI/CD secret injection.

### 2. Containerize the app

Create a production Dockerfile for the web app and workers. Example structure:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_multiagent.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Also create worker images when separating background tasks from Streamlit app execution.

### 3. Build and push the image

Example commands:

```bash
az acr build --registry myregistry --image ai-test-engine:latest .
```

or using Docker directly:

```bash
docker build -t ai-test-engine:latest .
docker tag ai-test-engine:latest myregistry.azurecr.io/ai-test-engine:latest
docker push myregistry.azurecr.io/ai-test-engine:latest
```

### 4. Provision infrastructure

Provision the following resources:

- Container app or App Service
- Managed database
- Redis or message queue
- Object storage
- Monitoring workspace
- Key Vault and identity assignments

### 5. Deploy the app

For Azure Container Apps, a typical deployment flow is:

```bash
az containerapp create \
  --name ai-test-engine-app \
  --resource-group rg-ai-test-engine \
  --environment my-container-env \
  --image myregistry.azurecr.io/ai-test-engine:latest \
  --target-port 8501 \
  --ingress external
```

For Azure App Service, deploy from a container or code pipeline and configure environment variables and managed identity.

### 6. Configure workers

Create a second deployment or background job for coordinator and execution workers. These workers should process queued test tasks, run browser and API automation jobs, and generate reports.

### 7. Enable monitoring and alerting

Set up:

- health checks
- response-time tracking
- queue depth monitoring
- failed job alerts
- logs for browser automation exceptions
- scheduled retry alerts

## Security checklist

Before going live, verify the following:

- Secrets are stored in Key Vault or a secret manager
- No credentials are committed to GitHub
- Access control is enabled for dashboards and admin workflows
- Input validation is enforced for test-generation prompts and uploaded files
- Data retention policies are defined for reports and logs
- HTTPS is enforced in production
- Least-privilege permissions are assigned to infrastructure identities

## Scaling recommendations

- Run the web dashboard in a horizontally scalable mode
- Keep workers independent so test jobs can scale separately
- Use a queue to decouple the API layer from execution
a- Keep browser automation isolated to dedicated worker pools to avoid resource contention
- Add autoscaling thresholds for queue length and CPU utilization

## CI/CD recommendations

Use a pipeline that performs the following:

1. Install dependencies
2. Run unit tests and validation checks
3. Build Docker images
4. Run secure scans
5. Deploy to staging
6. Run smoke tests
7. Promote to production

Example GitHub Actions stages:

- lint
- unit tests
- integration checks
- build image
- deploy to staging
- production approval gate

## Production operations checklist

- Set up production log retention and dashboards
- Define a rollback procedure
- Create alert thresholds for failed runs and queue delays
- Establish an incident response flow for operator actions
- Keep environment-specific config isolated per deployment stage

## Business rollout plan

1. Deploy to a staging environment with representative workloads
2. Validate web and API execution under realistic traffic
3. Confirm report generation and downloads
4. Review user access, audit, and security posture
5. Launch internal pilot customers
6. Expand to production multi-customer or multi-team deployment

## Recommended next steps for this repository

- Split runtime, dev, and test dependencies
- Add a real database model for projects, environments, and runs
- Add a task queue with worker pools
- Harden the web app and worker APIs
- Add CI/CD and environment config templates
- Create production dashboard and admin screens

## Conclusion

This project is a good foundation for an AI-powered testing product. To sell it commercially, it should be deployed as a managed, multi-tenant, cloud-hosted platform with secure operations, persistent data, and scalable workers. The stack above is the recommended path for a production-ready business launch.
