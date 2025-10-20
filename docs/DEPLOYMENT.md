# Deployment Guide

Complete guide for deploying AlkenaCode Adaptive Learning Platform to production.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
  - [AWS](#aws-deployment)
  - [Google Cloud](#google-cloud-deployment)
  - [DigitalOcean](#digitalocean-deployment)
- [Database Setup](#database-setup)
- [Security Hardening](#security-hardening)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Deployment Options

### Recommended Production Setup

```
┌──────────────────────────────────────┐
│         Load Balancer (HTTPS)        │
│         (nginx/Caddy/ALB)            │
└────────┬─────────────────────────────┘
         │
    ┌────▼────────────────────┐
    │   Frontend Containers   │
    │   (3+ replicas)         │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │   Backend Containers    │
    │   (3+ replicas)         │
    └────┬────────────────────┘
         │
    ┌────▼──────────────┬─────────────┐
    │                   │             │
┌───▼──────────┐  ┌────▼────────┐ ┌──▼──────────┐
│ PostgreSQL   │  │    Redis    │ │  S3/Storage │
│ (Managed DB) │  │  (Managed)  │ │  (Assets)   │
└──────────────┘  └─────────────┘ └─────────────┘
```

### Deployment Tiers

| Tier | Users | Setup | Cost (est.) |
|------|-------|-------|-------------|
| **Development** | 1-10 | Docker Compose on single VPS | $5-10/mo |
| **Small Production** | 10-1000 | Docker Compose + managed DB | $50-100/mo |
| **Medium Production** | 1000-10k | Kubernetes + managed services | $500-1k/mo |
| **Enterprise** | 10k+ | Auto-scaling + CDN + monitoring | $2k+/mo |

---

## Prerequisites

### Required Accounts

1. **Cloud Provider**
   - AWS / GCP / Azure / DigitalOcean

2. **Domain & DNS**
   - Registered domain (e.g., alkenacode.com)
   - DNS management (Cloudflare recommended)

3. **SSL Certificate**
   - Let's Encrypt (free, auto-renewal)
   - Or cloud provider certificate

4. **External Services**
   - OpenRouter API account
   - Email service (SendGrid/AWS SES) for notifications (optional)
   - Monitoring service (DataDog/New Relic) (optional)

### Required Tools

```bash
# Docker & Docker Compose
docker --version  # 20.10+
docker compose version  # v2.0+

# Cloud CLI (choose one)
aws --version     # AWS CLI
gcloud --version  # Google Cloud SDK
doctl --version   # DigitalOcean CLI

# Kubernetes (if using)
kubectl version   # 1.24+
helm version      # 3.0+

# Other tools
git --version
```

---

## Environment Setup

### 1. Production Environment Variables

Create `multiagential/backend/.env.production`:

```bash
# ============================================
# PRODUCTION ENVIRONMENT VARIABLES
# ============================================

# API Keys
OPENROUTER_API_KEY=sk-or-v1-your-production-key-here

# Database (use managed PostgreSQL)
DATABASE_URL=postgresql://user:password@db-host.region.provider.com:5432/adaptive_learning

# Redis (use managed Redis)
REDIS_URL=redis://redis-host.region.provider.com:6379

# Security
SECRET_KEY=generate-strong-random-secret-key-here
ALLOWED_HOSTS=api.alkenacode.com,alkenacode.com

# CORS (adjust for your domain)
CORS_ORIGINS=https://alkenacode.com,https://www.alkenacode.com

# LLM Configuration
DEFAULT_MODEL=openai/gpt-oss-120b
FALLBACK_MODELS=nousresearch/deephermes-3-mistral-24b-preview,google/gemini-2.5-flash-lite

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://...@sentry.io/...  # Optional error tracking

# Email (optional)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Feature Flags
ENABLE_RATE_LIMITING=true
ENABLE_CACHING=true
CACHE_TTL_PROFILE=3600
CACHE_TTL_JOURNEY=1800

# Performance
MAX_WORKERS=4
DB_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
```

### 2. Frontend Environment Variables

Create `multiagential/frontend/.env.production`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.alkenacode.com

# Analytics (optional)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HOTJAR_ID=your-hotjar-id

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=true

# Build Configuration
NODE_ENV=production
```

### 3. Generate Secrets

```bash
# Secret key (Python)
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# PostgreSQL password
openssl rand -base64 32

# Redis password (if needed)
openssl rand -base64 24
```

---

## Docker Deployment

### Production Docker Compose

Create `multiagential/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    image: alkenacode/backend:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - ./backend/.env.production
    depends_on:
      - postgres
      - redis
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    image: alkenacode/frontend:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    env_file:
      - ./frontend/.env.production
    depends_on:
      - backend
    networks:
      - frontend
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/dhparam.pem:/etc/nginx/dhparam.pem:ro
    depends_on:
      - backend
      - frontend
    networks:
      - frontend
      - backend
    restart: always

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: adaptive_learning
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    networks:
      - backend
    restart: always
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: always

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

### Production Dockerfile (Backend)

Create `multiagential/backend/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Production Dockerfile (Frontend)

Create `multiagential/frontend/Dockerfile.prod`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source
COPY . .

# Build application
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 3000

CMD ["npm", "start"]
```

### Nginx Configuration

Create `multiagential/nginx/nginx.conf`:

```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend {
    least_conn;
    server frontend:3000 max_fails=3 fail_timeout=30s;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name alkenacode.com www.alkenacode.com api.alkenacode.com;
    return 301 https://$server_name$request_uri;
}

# Frontend (HTTPS)
server {
    listen 443 ssl http2;
    server_name alkenacode.com www.alkenacode.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_dhparam /etc/nginx/dhparam.pem;

    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}

# Backend API (HTTPS)
server {
    listen 443 ssl http2;
    server_name api.alkenacode.com;

    # SSL Configuration (same as frontend)
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_dhparam /etc/nginx/dhparam.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;

    # CORS Headers (if needed)
    add_header Access-Control-Allow-Origin "https://alkenacode.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization, x-user-key" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

    location / {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;  # LLM requests can take time
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;

        # Large request body for quiz submissions
        client_max_body_size 10M;
    }

    # Health check endpoint (no rate limiting)
    location = / {
        proxy_pass http://backend;
        access_log off;
    }
}
```

### Deploy to VPS

```bash
# 1. SSH into VPS
ssh root@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clone repository
git clone https://github.com/yourusername/alkenacode-adaptive-learning.git
cd alkenacode-adaptive-learning/multiagential

# 4. Set up environment variables
nano backend/.env.production
nano frontend/.env.production

# 5. Generate SSL certificates (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d alkenacode.com -d www.alkenacode.com -d api.alkenacode.com

# 6. Copy certificates to nginx directory
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/alkenacode.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/alkenacode.com/privkey.pem nginx/ssl/

# 7. Generate DH parameters
openssl dhparam -out nginx/dhparam.pem 2048

# 8. Build and start services
docker compose -f docker-compose.prod.yml up -d --build

# 9. Initialize database
docker compose -f docker-compose.prod.yml exec backend python init_db.py

# 10. Check logs
docker compose -f docker-compose.prod.yml logs -f

# 11. Set up auto-renewal for SSL
sudo crontab -e
# Add: 0 0 1 * * certbot renew --quiet && docker compose -f /path/to/multiagential/docker-compose.prod.yml exec nginx nginx -s reload
```

---

## Cloud Deployment

### AWS Deployment

#### Architecture

```
Internet → Route53 → ALB → ECS Fargate
                           ├─ Backend (3+ tasks)
                           └─ Frontend (2+ tasks)
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
            RDS PostgreSQL    ElastiCache      S3 Bucket
            (Multi-AZ)         Redis           (Assets)
```

#### Setup

```bash
# 1. Install AWS CLI
pip install awscli
aws configure

# 2. Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier alkenacode-db \
    --db-instance-class db.t3.small \
    --engine postgres \
    --engine-version 16.1 \
    --master-username admin \
    --master-user-password YourStrongPassword \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --multi-az

# 3. Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id alkenacode-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 1

# 4. Push Docker images to ECR
aws ecr create-repository --repository-name alkenacode/backend
aws ecr create-repository --repository-name alkenacode/frontend

$(aws ecr get-login --no-include-email)

docker tag alkenacode/backend:latest xxxxx.dkr.ecr.region.amazonaws.com/alkenacode/backend:latest
docker push xxxxx.dkr.ecr.region.amazonaws.com/alkenacode/backend:latest

docker tag alkenacode/frontend:latest xxxxx.dkr.ecr.region.amazonaws.com/alkenacode/frontend:latest
docker push xxxxx.dkr.ecr.region.amazonaws.com/alkenacode/frontend:latest

# 5. Create ECS cluster
aws ecs create-cluster --cluster-name alkenacode-cluster

# 6. Create task definitions
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 7. Create ECS services
aws ecs create-service \
    --cluster alkenacode-cluster \
    --service-name backend-service \
    --task-definition alkenacode-backend \
    --desired-count 3 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx]}"

# 8. Set up Application Load Balancer
aws elbv2 create-load-balancer \
    --name alkenacode-alb \
    --subnets subnet-xxxxx subnet-yyyyy \
    --security-groups sg-xxxxx

# 9. Configure Route53
aws route53 create-hosted-zone --name alkenacode.com --caller-reference $(date +%s)
```

**Estimated Monthly Cost**:
- RDS t3.small (Multi-AZ): ~$60
- ElastiCache t3.micro: ~$12
- ECS Fargate (5 tasks): ~$150
- ALB: ~$20
- Data transfer: ~$20
- **Total**: ~$260/month

---

### Google Cloud Deployment

#### Architecture

```
Internet → Cloud Load Balancing → Cloud Run
                                  ├─ Backend (auto-scale)
                                  └─ Frontend (auto-scale)
                                         │
                        ┌────────────────┼────────────────┐
                        │                │                │
                   Cloud SQL          Memorystore     Cloud Storage
                   PostgreSQL            Redis          (Assets)
```

#### Setup

```bash
# 1. Install gcloud CLI
curl https://sdk.cloud.google.com | bash
gcloud init

# 2. Create Cloud SQL PostgreSQL instance
gcloud sql instances create alkenacode-db \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YourStrongPassword \
    --backup \
    --enable-bin-log

# 3. Create Memorystore Redis instance
gcloud redis instances create alkenacode-redis \
    --size=1 \
    --region=us-central1 \
    --tier=basic

# 4. Build and push images to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/backend ./backend
gcloud builds submit --tag gcr.io/PROJECT_ID/frontend ./frontend

# 5. Deploy to Cloud Run
gcloud run deploy backend \
    --image gcr.io/PROJECT_ID/backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL=...,REDIS_URL=...

gcloud run deploy frontend \
    --image gcr.io/PROJECT_ID/frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_API_URL=...

# 6. Set up custom domain
gcloud run domain-mappings create \
    --service=frontend \
    --domain=alkenacode.com \
    --region=us-central1
```

**Estimated Monthly Cost**:
- Cloud SQL db-f1-micro: ~$10
- Memorystore Basic 1GB: ~$35
- Cloud Run (5k requests/day): ~$20
- **Total**: ~$65/month (scales with usage)

---

### DigitalOcean Deployment

#### Simplest Production Setup

```bash
# 1. Create Droplet (8GB RAM recommended)
doctl compute droplet create alkenacode \
    --size s-4vcpu-8gb \
    --image docker-20-04 \
    --region nyc1 \
    --ssh-keys YOUR_SSH_KEY_ID

# 2. Create Managed PostgreSQL
doctl databases create alkenacode-db \
    --engine pg \
    --version 16 \
    --size db-s-1vcpu-1gb \
    --region nyc1

# 3. Create Managed Redis
doctl databases create alkenacode-redis \
    --engine redis \
    --version 7 \
    --size db-s-1vcpu-1gb \
    --region nyc1

# 4. SSH into Droplet and deploy (same as VPS deployment above)
```

**Estimated Monthly Cost**:
- Droplet 8GB: ~$48
- Managed PostgreSQL: ~$15
- Managed Redis: ~$15
- **Total**: ~$78/month

---

## Security Hardening

### 1. Environment Variables

```bash
# Never commit .env files
echo ".env*" >> .gitignore

# Use secrets management
# AWS: Secrets Manager
# GCP: Secret Manager
# DO: App Platform Secrets
```

### 2. Database Security

```sql
-- Create read-only user for reporting
CREATE USER alkenacode_readonly WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE adaptive_learning TO alkenacode_readonly;
GRANT USAGE ON SCHEMA public TO alkenacode_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO alkenacode_readonly;

-- Enable SSL connections
ALTER SYSTEM SET ssl = on;

-- Restrict connections
-- Edit pg_hba.conf: hostssl all all 0.0.0.0/0 md5
```

### 3. API Security

```python
# Add rate limiting (main.py)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/adaptive/onboarding")
@limiter.limit("10/hour")  # 10 onboardings per hour per IP
async def onboarding_endpoint(request: Request):
    pass
```

### 4. Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Deny direct access to services
sudo ufw deny 5432  # PostgreSQL
sudo ufw deny 6379  # Redis
sudo ufw deny 8000  # Backend (use nginx proxy)
```

---

## Monitoring & Logging

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

### Application Logs

```python
# Configure structured logging (main.py)
import logging
import sys
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[logHandler])

logger = logging.getLogger(__name__)

# Log with context
logger.info("Quiz submitted", extra={
    "user_id": user_id,
    "quiz_id": quiz_id,
    "score": score,
    "duration_seconds": duration
})
```

### Health Checks

```python
# Add detailed health endpoint
@app.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgres": await check_postgres(),
            "redis": await check_redis(),
            "openrouter": await check_openrouter()
        },
        "metrics": {
            "active_users": await count_active_users(),
            "cache_hit_rate": await get_cache_hit_rate(),
            "avg_response_time_ms": await get_avg_response_time()
        }
    }
```

---

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="alkenacode_backup_$DATE.sql"

# Backup
docker compose exec -T postgres pg_dump -U adaptive_user adaptive_learning > "$BACKUP_DIR/$FILENAME"

# Compress
gzip "$BACKUP_DIR/$FILENAME"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/$FILENAME.gz" s3://alkenacode-backups/postgres/

# Delete local backups older than 7 days
find $BACKUP_DIR -name "*.gz" -type f -mtime +7 -delete

# Cron: 0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Restore database
gunzip alkenacode_backup_20251019_020000.sql.gz
docker compose exec -T postgres psql -U adaptive_user adaptive_learning < alkenacode_backup_20251019_020000.sql
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale backend replicas
docker compose -f docker-compose.prod.yml up -d --scale backend=5

# Scale frontend replicas
docker compose -f docker-compose.prod.yml up -d --scale frontend=3
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## CI/CD Pipeline

### GitHub Actions

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd multiagential/backend
          pip install -r requirements.txt
          pytest tests/

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push backend
        run: |
          cd multiagential/backend
          docker build -f Dockerfile.prod -t alkenacode/backend:latest .
          docker push alkenacode/backend:latest

      - name: Build and push frontend
        run: |
          cd multiagential/frontend
          docker build -f Dockerfile.prod -t alkenacode/frontend:latest .
          docker push alkenacode/frontend:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app/alkenacode-adaptive-learning/multiagential
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d
            docker compose -f docker-compose.prod.yml exec backend python init_db.py
```

---

## Post-Deployment Checklist

- [ ] SSL certificates installed and auto-renewing
- [ ] DNS records configured correctly
- [ ] Environment variables set securely
- [ ] Database backups scheduled
- [ ] Monitoring and alerts configured
- [ ] Logs centralized and accessible
- [ ] Firewall rules applied
- [ ] Rate limiting enabled
- [ ] Health checks responding correctly
- [ ] Performance tested under load
- [ ] Disaster recovery plan documented

---

**Last Updated**: October 19, 2025
