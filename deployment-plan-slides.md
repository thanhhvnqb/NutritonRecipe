# Recipe Cost & Nutrition API
## Cloud Deployment Plan

**FastAPI-based Microservice**  
ML-Powered Ingredient Substitution & Cost Analysis

---

## Executive Summary

### Project Overview
Deploy a production-ready Recipe Cost & Nutrition API to the cloud with high availability, scalability, and cost optimization.

### Key Objectives
- 🚀 **High Availability:** 99.9% uptime SLA
- 📈 **Scalability:** Auto-scaling based on demand
- 💰 **Cost Optimization:** Pay-as-you-use model
- 🔒 **Security:** Enterprise-grade security controls
- 📊 **Monitoring:** Comprehensive observability

### Expected Benefits
- Reduced operational overhead
- Improved performance and reliability
- Global accessibility
- Automated backup and disaster recovery

---

## Current Application Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   FastAPI App   │    │   Redis Cache   │
│   (Port 80)     │───▶│   (Port 8000)   │───▶│   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  SQLite Database│
                       │   (recipe.db)   │
                       └─────────────────┘
```

### Technology Stack
- **FastAPI** - Python Web Framework
- **SQLite** - Local Database
- **Redis** - Caching Layer
- **Nginx** - Reverse Proxy
- **Docker** - Containerization
- **PyTorch** - Deep Learning Framework for ML Processing

---

## Proposed Cloud Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Internet                             │
                    └─────────────────────┬───────────────────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────────────────┐
                    │                Load Balancer                            │
                    │            (Application Gateway)                        │
                    └─────────────────────┬───────────────────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────────────────┐
                    │                  API Gateway                            │
                    │         (Rate Limiting, Authentication)                 │
                    └─────────────────────┬───────────────────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────────────────┐
                    │              Container Instances                        │
                    │  ┌─────────────────┐       ┌─────────────────┐         │
                    │  │   FastAPI APIs  │       │  PyTorch ML     │         │
                    │  │  ┌───┐ ┌───┐    │       │   Service       │         │
                    │  │  │API│ │API│    │◄─────►│  ┌───┐ ┌───┐    │         │
                    │  │  │ 1 │ │ N │    │       │  │ML │ │ML │    │         │
                    │  │  └───┘ └───┘    │       │  │ 1 │ │ N │    │         │
                    │  └─────────────────┘       │  └───┘ └───┘    │         │
                    │                            └─────────────────┘         │
                    └─────────────────────┬───────────────────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────────────────┐
                    │                Data Layer                               │
                    │  ┌─────────────┐              ┌─────────────┐          │
                    │  │  PostgreSQL │              │    Redis    │          │
                    │  │  (Primary)  │              │   Cluster   │          │
                    │  └─────────────┘              └─────────────┘          │
                    └─────────────────────────────────────────────────────────┘
```

---

## Cloud Provider Comparison

| Feature | AWS | Azure | Google Cloud |
|---------|-----|-------|--------------|
| **Container Service** | ECS Fargate | Container Instances | Cloud Run |
| **Database** | RDS PostgreSQL | Azure Database | Cloud SQL |
| **Cache** | ElastiCache Redis | Azure Cache for Redis | Memorystore |
| **Load Balancer** | Application Load Balancer | Application Gateway | Cloud Load Balancing |
| **GPU Support** | Fargate GPU tasks | Container Instances GPU | Cloud Run GPU (Preview) |
| **ML Model Serving** | SageMaker | ML Studio | Vertex AI |
| **Estimated Monthly Cost** | $180-350 | $170-320 | $150-300 |

**Recommendation:** Google Cloud Platform for cost-effectiveness and excellent container support with Cloud Run.

---

## Recommended: Google Cloud Deployment

### Why Google Cloud?
- 🏃‍♂️ **Cloud Run:** Serverless containers with automatic scaling
- 💰 **Cost-Effective:** Pay only for actual usage
- 🔧 **Easy Setup:** Minimal configuration required
- 🌍 **Global CDN:** Built-in content delivery
- 📊 **Excellent Monitoring:** Integrated with Google Cloud Operations

### Architecture Components
- **Cloud Run (API Service):** Serverless container for FastAPI application (CPU-optimized)
- **Cloud Run (ML Service):** Serverless container for PyTorch inference (GPU-enabled)
- **Cloud SQL:** Managed PostgreSQL database
- **Memorystore:** Managed Redis for caching
- **Cloud Load Balancing:** Global load balancer with SSL termination
- **Cloud Build:** CI/CD pipeline for automated deployments
- **Service-to-Service Communication:** Internal HTTP/gRPC for ML inference calls

---

## Migration Strategy

### Database Migration
1. **Export SQLite data to CSV/SQL format**
   ```bash
   sqlite3 recipe.db ".dump" > backup.sql
   ```
2. **Create Cloud SQL PostgreSQL instance**
3. **Update SQLAlchemy connection string**
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@host/db"
   ```
4. **Import data using Cloud SQL proxy**

### Application Updates Required
- Update database connection configuration
- Add health check endpoints for Cloud Run
- Configure environment variables for secrets
- Update Redis connection for Memorystore
- **Microservices Architecture:** Split application into API and ML service components
- **Service Communication:** Implement HTTP/gRPC client for ML service communication
- **Circuit Breaker:** Add fault tolerance for ML service calls with fallback mechanisms
- **ML Service API:** Create dedicated FastAPI endpoints for PyTorch inference
- **Model Loading:** Implement efficient model loading and warm-up in ML service
- **PyTorch Model Optimization:** Convert models to TorchScript for production serving
- **GPU Configuration:** Add CUDA support and GPU memory management
- **Model Caching:** Implement PyTorch model caching strategy for faster inference

---

## Deployment Timeline

### Week 1: Infrastructure Setup
- Create GCP project and enable APIs
- Set up Cloud SQL PostgreSQL instance
- Configure Memorystore Redis
- Create service accounts and IAM roles

### Week 2: Application Migration
- **Microservices Separation:** Split monolithic application into API and ML services
- **Service Communication:** Implement HTTP client for inter-service communication
- **API Service:** Update main FastAPI app to call external ML service
- **ML Service:** Create dedicated PyTorch inference service with FastAPI
- **PyTorch Model Optimization:** Convert models to TorchScript and implement quantization
- **GPU Integration:** Configure CUDA support and optimize memory usage for ML service
- Migrate database schema and data
- Set up Cloud Build CI/CD pipeline for both services
- Configure environment variables and secrets for both services

### Week 3: Testing & Optimization
- Deploy to staging environment
- Performance testing and optimization
- Security testing and compliance
- Load testing with realistic traffic

### Week 4: Production Deployment
- Production deployment
- DNS configuration and SSL setup
- Monitoring and alerting setup
- Documentation and team training

---

## Security & Compliance

### Security Measures
- **Identity & Access:** Google Cloud IAM, Service Accounts
- **Network Security:** VPC with Private IPs, Cloud Armor WAF
- **Data Protection:** Encryption at Rest, Encryption in Transit
- **API Security:** Rate Limiting, API Keys/OAuth

### Compliance Features
- 🔐 **Data Encryption:** AES-256 encryption for data at rest and in transit
- 📋 **Audit Logging:** Comprehensive audit trails with Cloud Audit Logs
- 🛡️ **Access Controls:** Role-based access control (RBAC)
- 🔍 **Vulnerability Scanning:** Container image scanning
- 📊 **Compliance:** SOC 2, ISO 27001, GDPR ready

---

## Monitoring & Observability

### Monitoring Stack
**Google Cloud Operations Suite**
- Cloud Monitoring for metrics and dashboards
- Cloud Logging for centralized log management
- Cloud Trace for distributed tracing
- Error Reporting for exception tracking

### Key Metrics to Monitor
- **Application Metrics:** Response Time, Request Rate, Error Rate
- **Infrastructure Metrics:** CPU Usage, Memory Usage, Network I/O
- **Database Metrics:** Connection Pool, Query Performance, Storage Usage
- **Business Metrics:** API Usage, Recipe Calculations, Cache Hit Rate

### Alerting Strategy
- 🚨 **Critical:** Service down, high error rate (>5%)
- ⚠️ **Warning:** High latency (>2s), resource usage (>80%)
- 📊 **Info:** Deployment notifications, scaling events

---

## Cost Analysis & Optimization

### Estimated Monthly Costs (Google Cloud)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| Cloud Run (API Service) | 2 vCPU, 4GB RAM, 1M requests | $50-80 |
| Cloud Run (ML Service) | 4 vCPU, 8GB RAM, T4 GPU | $80-150 |
| Cloud SQL (PostgreSQL) | db-f1-micro, 10GB storage | $25-35 |
| Memorystore (Redis) | 1GB Basic tier | $30-40 |
| Load Balancer | Global HTTP(S) LB | $15-25 |
| Monitoring & Logging | Standard tier | $15-25 |
| **Total** | | **$215-355** |

### Cost Optimization Strategies
- 💰 **Auto-scaling:** Scale to zero when not in use (especially for ML service)
- 📊 **Resource optimization:** Right-size based on usage patterns for each service
- 🔄 **Caching:** Reduce ML inference calls with Redis caching
- 📈 **Monitoring:** Set up budget alerts and cost tracking per service
- 🎯 **Smart Routing:** Route only ML-requiring requests to GPU service
- 🔄 **Model Caching:** Cache model outputs to reduce GPU usage

---

## Disaster Recovery & Backup

### Backup Strategy
**Database Backups**
- Automated daily backups with 30-day retention
- Point-in-time recovery capability
- Cross-region backup replication

**Application Backups**
- Container images stored in Container Registry
- Configuration stored in version control
- Infrastructure as Code (Terraform)

### Recovery Procedures
- **RTO: 15 minutes** - Recovery Time Objective for application restoration
- **RPO: 1 hour** - Recovery Point Objective for data loss tolerance
- **Multi-Region Setup** - Standby deployment in secondary region for critical scenarios

---

## CI/CD Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   GitHub    │───▶│ Cloud Build │───▶│   Testing   │───▶│ Cloud Run   │
│ Repository  │    │   Trigger   │    │Environment  │    │ Production  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                            │                                    │
                            ▼                                    ▼
                   ┌─────────────┐                      ┌─────────────┐
                   │   Security  │                      │ Monitoring  │
                   │   Scanning  │                      │ & Alerting  │
                   └─────────────┘                      └─────────────┘
```

### Pipeline Stages
1. **Code Commit:** Developer pushes code to GitHub
2. **Build Trigger:** Cloud Build automatically triggered
3. **Testing:** Run unit tests, integration tests, security scans
4. **Build Image:** Create container image and push to registry
5. **Deploy:** Deploy to staging, then production after approval
6. **Monitor:** Automated health checks and monitoring

---

## Performance Optimization

### Application-Level Optimizations
- 🚀 **Async Processing:** FastAPI async endpoints for I/O operations
- 🧠 **PyTorch Model Optimization:** TorchScript compilation and model quantization
- 🎯 **GPU Acceleration:** CUDA-optimized inference for ingredient similarity calculations
- 📊 **Database Optimization:** Proper indexing and query optimization
- 🔄 **Redis Caching:** Cache frequently accessed data and pre-computed model outputs

### Infrastructure Optimizations
- **Auto-scaling:** Scale based on CPU/Memory (Min: 0, Max: 100 instances)
- **Connection Pooling:** Optimize database connections, reduce overhead
- **CDN Integration:** Cache static responses, global edge locations
- **Compression:** Gzip response compression, reduce bandwidth usage

### Expected Performance Improvements
- 📈 **Response Time:** <95ms (vs 200ms+ locally)
- 🔄 **Throughput:** 1000+ requests/second
- 🌍 **Global Latency:** <100ms worldwide
- ⚡ **Cache Hit Rate:** >90% for ingredient data

---

## Risk Assessment & Mitigation

### Identified Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Service Outage | High | Low | Multi-region deployment, health checks |
| Data Loss | High | Very Low | Automated backups, point-in-time recovery |
| Security Breach | High | Low | IAM, encryption, security scanning |
| Cost Overrun | High | Medium | Budget alerts, auto-scaling limits, GPU monitoring |
| Performance Issues | Medium | Low | Load testing, monitoring, caching |
| GPU Memory Issues | Medium | Medium | Memory monitoring, model optimization, fallback to CPU |
| Service Communication Failure | Medium | Medium | Circuit breaker, retry logic, cached fallbacks |
| ML Service Latency | Medium | Medium | Model optimization, connection pooling, caching |

### Contingency Plans
- 🔄 **Rollback Strategy:** Automated rollback on deployment failures
- 📞 **Incident Response:** 24/7 monitoring with escalation procedures
- 🔧 **Maintenance Windows:** Scheduled maintenance with zero-downtime deployments
- 📋 **Documentation:** Comprehensive runbooks and troubleshooting guides

---

## Implementation Steps

### Phase 1: Infrastructure Setup (Week 1)

**Day 1-2: GCP Project Setup**
```bash
# Create project and enable APIs
gcloud projects create recipe-api-prod
gcloud services enable run.googleapis.com sql-component.googleapis.com
```

**Day 3-4: Database Setup**
```bash
# Create Cloud SQL instance
gcloud sql instances create recipe-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1
```

**Day 5-7: Redis and Networking**
```bash
# Create Memorystore Redis instance
gcloud redis instances create recipe-cache \
  --size=1 \
  --region=us-central1
```

### Phase 2: Application Migration (Week 2)
- **Microservices Separation:** Split monolithic application into API and ML services
- **Service Communication:** Implement HTTP client for inter-service communication
- **API Service:** Update main FastAPI app to call external ML service
- **ML Service:** Create dedicated PyTorch inference service with FastAPI
- **PyTorch Model Optimization:** Convert models to TorchScript and implement quantization
- **GPU Integration:** Configure CUDA support and optimize memory usage for ML service
- Migrate database schema and data
- Set up Cloud Build CI/CD pipeline for both services
- Configure environment variables and secrets for both services

---

## Success Metrics & KPIs

### Technical Metrics
- **Availability:** Target 99.9% (Maximum 8.76 hours downtime/year)
- **Response Time:** Target <100ms (95th percentile)
- **Throughput:** Target 1000 RPS (Peak capacity)
- **Error Rate:** Target <0.1% (Application errors)

### Business Metrics
- 📊 **API Usage Growth:** Track monthly active users and requests
- 💰 **Cost Efficiency:** Cost per request and total infrastructure cost
- 🔄 **Feature Adoption:** Usage of ingredient substitution and cost calculation
- 🌍 **Global Reach:** Geographic distribution of API usage

### Operational Metrics
- ⚡ **Deployment Frequency:** Target weekly releases
- 🔧 **Mean Time to Recovery:** <15 minutes for incidents
- 🛡️ **Security Compliance:** Zero critical vulnerabilities
- 📈 **Team Productivity:** Reduced operational overhead

---

## Next Steps & Action Items

### Immediate Actions (This Week)
1. **Stakeholder Approval:** Get approval for cloud migration plan and budget
2. **Team Assignment:** Assign team members to specific tasks
3. **GCP Account Setup:** Create Google Cloud account and billing setup
4. **Environment Planning:** Plan development, staging, and production environments

### Week 1 Deliverables
- ✅ GCP project created with proper IAM setup
- ✅ Cloud SQL PostgreSQL instance provisioned
- ✅ Memorystore Redis instance configured
- ✅ Basic monitoring and alerting setup

### Success Criteria
- 🎯 **Zero-downtime migration** from current infrastructure
- 📈 **Performance improvement** of at least 50%
- 💰 **Cost optimization** within projected budget
- 🔒 **Security compliance** with enterprise standards
- 📊 **Comprehensive monitoring** and alerting in place

---

## Questions & Discussion

### Thank you!
Ready to deploy the Recipe Cost & Nutrition API to the cloud

**Contact Information:**
- 📧 Email: deployment-team@company.com
- 📱 Slack: #recipe-api-deployment
- 📋 Project Board: GitHub Projects

---

## Appendix: Technical Details

### Environment Variables Configuration

**API Service Environment Variables**
```bash
# API Service environment variables
DATABASE_URL=postgresql://user:password@host:5432/recipe_db
REDIS_URL=redis://memorystore-ip:6379
ML_SERVICE_URL=https://ml-service-url.run.app
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**ML Service Environment Variables**
```bash
# ML Service environment variables
REDIS_URL=redis://memorystore-ip:6379
ENVIRONMENT=production
LOG_LEVEL=INFO
# PyTorch specific configurations
TORCH_JIT=1
OMP_NUM_THREADS=1
CUDA_VISIBLE_DEVICES=0
PYTORCH_TRANSFORMERS_CACHE=/tmp/transformers_cache
MODEL_CACHE_DIR=/app/models
```

### Docker Configuration for Cloud Run

**API Service (api-service/Dockerfile)**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt
COPY ./api-service .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**ML Service (ml-service/Dockerfile)**
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
WORKDIR /app
COPY requirements-ml.txt .
RUN pip install -r requirements-ml.txt
COPY ./ml-service .
# Optimize PyTorch for production
ENV TORCH_JIT=1
ENV OMP_NUM_THREADS=1
EXPOSE 8080
CMD ["uvicorn", "ml_main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Build Configuration
```yaml
steps:
  # Build API Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/recipe-api-service', '-f', 'api-service/Dockerfile', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/recipe-api-service']
  
  # Build ML Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/recipe-ml-service', '-f', 'ml-service/Dockerfile', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/recipe-ml-service']
  
  # Deploy API Service
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'recipe-api-service', 
           '--image', 'gcr.io/$PROJECT_ID/recipe-api-service', 
           '--region', 'us-central1',
           '--set-env-vars', 'ML_SERVICE_URL=https://recipe-ml-service-url.run.app']
  
  # Deploy ML Service
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'recipe-ml-service', 
           '--image', 'gcr.io/$PROJECT_ID/recipe-ml-service', 
           '--region', 'us-central1',
           '--cpu', '4', '--memory', '8Gi',
           '--gpu', '1', '--gpu-type', 'nvidia-tesla-t4']
```

---

## Microservices Architecture Benefits

### Separation of Concerns
- 🎯 **API Service:** Handles business logic, database operations, and HTTP routing
- 🧠 **ML Service:** Dedicated to PyTorch model inference and GPU optimization
- 📊 **Independent Scaling:** Scale ML service based on inference demand
- 💰 **Cost Efficiency:** GPU resources only allocated to ML workloads

### Technical Advantages
- **Resource Optimization:** CPU-optimized instances for API, GPU for ML
- **Fault Isolation:** API service remains operational if ML service fails
- **Technology Stack:** Different base images and dependencies per service
- **Development Velocity:** Teams can work independently on each service

### Service Communication
- **Protocol:** HTTP REST API for simplicity and debugging
- **Circuit Breaker:** Fault tolerance with fallback to cached results
- **Load Balancing:** Independent load balancing for each service
- **Monitoring:** Separate observability per service

--- 