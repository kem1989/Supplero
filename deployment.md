# 🚀 Supplero Deployment Guide

This guide covers multiple deployment options for the Supplero AI-powered procurement and supplier risk management platform.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Deployment Options](#deployment-options)
  - [Option 1: Docker Compose (Development/Testing/Staging)](#option-1-docker-compose-developmenttestingstaging) ⭐ **RECOMMENDED FOR TESTING**
  - [Option 2: Kubernetes (Production)](#option-2-kubernetes-production)
  - [Option 3: Cloud Platform Deployment](#option-3-cloud-platform-deployment)
- [Environment Configuration](#environment-configuration)
- [Security Considerations](#security-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start for Testing Users

**For testing with a small group of users, Docker Compose is the perfect solution!**

```bash
# 1. Set up your server
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh

# 2. Clone and configure
git clone <your-repo> && cd Supplero
cp env.example .env.testing
# Edit .env.testing with your settings

# 3. Deploy for testing
docker-compose -f docker-compose.testing.yml up -d

# 4. Access your app
# Frontend: http://your-server-ip:3000
# Backend: http://your-server-ip:8000
```

**Why Docker for Testing?**
- ✅ Simple setup and management
- ✅ Easy to scale up/down
- ✅ Perfect for small user groups (5-50 users)
- ✅ Quick updates and rollbacks
- ✅ No Kubernetes complexity
- ✅ Cost-effective

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ recommended (16GB+ for production)
- **Storage**: 50GB+ available space
- **OS**: Linux, macOS, or Windows with WSL2

### Required Software
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Node.js**: 18+ (for local development)
- **Python**: 3.11+ (for local development)
- **kubectl**: 1.25+ (for Kubernetes deployment)
- **Helm**: 3.0+ (optional, for advanced Kubernetes deployments)

### External Dependencies
- **OpenAI API Key**: Required for AI features
- **PostgreSQL**: 15+ (included in Docker setup)
- **Redis**: 7+ (included in Docker setup)
- **Elasticsearch**: 8.11+ (included in Docker setup)

## Architecture Overview

Supplero consists of the following microservices:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   PostgreSQL    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Database      │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         │              │     Cache       │              │
         │              │   Port: 6379    │              │
         │              └─────────────────┘              │
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│  Elasticsearch  │◄─────────────┘
                        │   Search Engine │
                        │   Port: 9200    │
                        └─────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Development/Testing/Staging)

**Best for**: Development, testing, small user groups, and staging environments

#### Quick Start for Testing
```bash
# Clone the repository
git clone <repository-url>
cd Supplero

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

#### Production-Ready Docker Compose for Testing

For testing with real users, you'll want to make some adjustments to your `docker-compose.yml`:

**Create a `docker-compose.testing.yml` file:**

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: supplero-postgres-testing
    environment:
      POSTGRES_DB: supplero
      POSTGRES_USER: supplero
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_testing_password_2024}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_testing:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - supplero-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U supplero"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: supplero-redis-testing
    ports:
      - "6379:6379"
    volumes:
      - redis_data_testing:/data
    networks:
      - supplero-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Backend API Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: supplero-backend-testing
    env_file:
      - .env
    environment:
      - POSTGRES_DB=supplero
      - POSTGRES_USER=supplero
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-secure_testing_password_2024}
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY:-secure_testing_secret_key_2024}
      - JWT_ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=60
      - ENVIRONMENT=testing
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/__pycache__
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    networks:
      - supplero-network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: supplero-frontend-testing
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://your-server-ip:8000}
      - INTERNAL_API_URL=http://backend:8000
      - NODE_ENV=production
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/app:/app/app
      - ./frontend/public:/app/public
      - ./frontend/tailwind.config.js:/app/tailwind.config.js
      - ./frontend/postcss.config.js:/app/postcss.config.js
      - ./frontend/next.config.js:/app/next.config.js
      - ./frontend/tsconfig.json:/app/tsconfig.json
    depends_on:
      - backend
    networks:
      - supplero-network
    command: npm run build && npm start
    restart: unless-stopped

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: supplero-elasticsearch-testing
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data_testing:/usr/share/elasticsearch/data
    networks:
      - supplero-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data_testing:
  redis_data_testing:
  elasticsearch_data_testing:

networks:
  supplero-network:
    driver: bridge
```

#### Testing Deployment Steps

1. **Prepare Your Server**
   ```bash
   # Update your server
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Configure Environment for Testing**
   ```bash
   # Create production environment file
   cp env.example .env.testing
   
   # Edit with production values
   nano .env.testing
   ```

   **Required changes for testing:**
   ```bash
   # .env.testing
   ENVIRONMENT=testing
   DEBUG=false
   LOG_LEVEL=INFO
   
   # Security (CHANGE THESE!)
   SECRET_KEY=your_very_secure_secret_key_for_testing
   POSTGRES_PASSWORD=your_secure_database_password
   
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   
   # Frontend URL (replace with your server's IP/domain)
   NEXT_PUBLIC_API_URL=http://your-server-ip:8000
   
   # Optional external APIs
   DUN_BRADSTREET_API_KEY=your_dun_bradstreet_key
   REFINITIV_API_KEY=your_refinitiv_key
   NEWS_API_KEY=your_news_api_key
   ```

3. **Deploy for Testing**
   ```bash
   # Start testing environment
   docker-compose -f docker-compose.testing.yml up -d
   
   # Check status
   docker-compose -f docker-compose.testing.yml ps
   
   # View logs
   docker-compose -f docker-compose.testing.yml logs -f
   ```

4. **Configure Firewall (if needed)**
   ```bash
   # Allow necessary ports
   sudo ufw allow 3000  # Frontend
   sudo ufw allow 8000  # Backend API
   sudo ufw allow 22    # SSH
   sudo ufw enable
   ```

5. **Set up Domain/SSL (Optional but Recommended)**
   ```bash
   # Install Nginx as reverse proxy
   sudo apt install nginx
   
   # Create Nginx config
   sudo nano /etc/nginx/sites-available/supplero
   ```

   **Nginx configuration:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       # Frontend
       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Backend API
       location /api/ {
           proxy_pass http://localhost:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   ```bash
   # Enable site
   sudo ln -s /etc/nginx/sites-available/supplero /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

#### Monitoring Your Testing Deployment

```bash
# Check all services
docker-compose -f docker-compose.testing.yml ps

# View logs
docker-compose -f docker-compose.testing.yml logs -f backend
docker-compose -f docker-compose.testing.yml logs -f frontend

# Check resource usage
docker stats

# Health checks
curl http://your-server-ip:8000/health
curl http://your-server-ip:3000
```

#### Backup and Updates

```bash
# Backup database
docker-compose -f docker-compose.testing.yml exec postgres pg_dump -U supplero supplero > backup_$(date +%Y%m%d).sql

# Update application
git pull
docker-compose -f docker-compose.testing.yml build
docker-compose -f docker-compose.testing.yml up -d

# Rollback if needed
docker-compose -f docker-compose.testing.yml down
# Restore from backup
```

#### Detailed Steps

1. **Environment Setup**
   ```bash
   # Copy and configure environment
   cp env.example .env
   
   # Edit .env file with your configuration
   nano .env
   ```

2. **Required Environment Variables**
   ```bash
   # OpenAI Configuration (Required)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Security (Change in production!)
   SECRET_KEY=your_very_secure_secret_key_here
   
   # Database (Default values work for development)
   POSTGRES_DB=supplero
   POSTGRES_USER=supplero
   POSTGRES_PASSWORD=supplero_dev
   
   # External APIs (Optional)
   DUN_BRADSTREET_API_KEY=your_dun_bradstreet_key
   REFINITIV_API_KEY=your_refinitiv_key
   NEWS_API_KEY=your_news_api_key
   ```

3. **Start Services**
   ```bash
   # Build and start all services
   docker-compose up -d --build
   
   # View logs
   docker-compose logs -f
   
   # Check health
   make health
   ```

4. **Access Services**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Elasticsearch: http://localhost:9200

#### Using Makefile Commands
```bash
# Start development environment
make dev

# View logs
make logs

# Run tests
make test

# Clean up
make clean

# Health check
make health
```

### Option 2: Kubernetes (Production)

**Best for**: Production deployments, scalability, high availability

#### Prerequisites
- Kubernetes cluster (1.25+)
- kubectl configured
- Container registry access (GitHub Container Registry)

#### Step 1: Prepare Container Images

1. **Build Production Images**
   ```bash
   # Build backend image
   docker build -f backend/Dockerfile.dev -t ghcr.io/supplero/backend:latest ./backend
   
   # Build frontend image
   docker build -f frontend/Dockerfile.dev -t ghcr.io/supplero/frontend:latest ./frontend
   ```

2. **Push to Registry**
   ```bash
   # Login to GitHub Container Registry
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   
   # Push images
   docker push ghcr.io/supplero/backend:latest
   docker push ghcr.io/supplero/frontend:latest
   ```

#### Step 2: Configure Secrets

1. **Create Namespace**
   ```bash
   kubectl create namespace supplero
   ```

2. **Create Secrets**
   ```bash
   # Create registry secret
   kubectl create secret docker-registry ghcr-secret \
     --docker-server=ghcr.io \
     --docker-username=YOUR_USERNAME \
     --docker-password=YOUR_TOKEN \
     --namespace=supplero
   
   # Create application secrets
   kubectl create secret generic backend-secret \
     --from-literal=secret-key="your_production_secret_key" \
     --from-literal=openai-api-key="your_openai_api_key" \
     --from-literal=postgres-password="your_secure_postgres_password" \
     --from-literal=redis-password="your_secure_redis_password" \
     --namespace=supplero
   ```

#### Step 3: Deploy Infrastructure

1. **Deploy Database and Cache**
   ```bash
   # Deploy PostgreSQL
   kubectl apply -f infrastructure/k8s/postgres.yaml
   
   # Deploy Redis
   kubectl apply -f kubernetes/redis.yaml
   
   # Deploy Elasticsearch
   kubectl apply -f kubernetes/elasticsearch.yaml
   ```

2. **Deploy Application Services**
   ```bash
   # Deploy Backend
   kubectl apply -f kubernetes/backend.yaml
   
   # Deploy Frontend
   kubectl apply -f kubernetes/frontend.yaml
   ```

3. **Verify Deployment**
   ```bash
   # Check all pods
   kubectl get pods -n supplero
   
   # Check services
   kubectl get services -n supplero
   
   # Check ingress
   kubectl get ingress -n supplero
   ```

#### Step 4: Configure Ingress

1. **Install NGINX Ingress Controller** (if not already installed)
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   ```

2. **Update DNS** (for production)
   ```bash
   # Add to your DNS provider or /etc/hosts
   your-domain.com -> ingress-ip
   api.your-domain.com -> ingress-ip
   ```

#### Using Makefile for Kubernetes
```bash
# Deploy everything
make k8s-deploy

# Delete everything
make k8s-delete

# Check deployment status
kubectl get all -n supplero
```

### Option 3: Cloud Platform Deployment

#### AWS EKS Deployment

1. **Create EKS Cluster**
   ```bash
   # Using eksctl
   eksctl create cluster --name supplero-cluster --region us-west-2 --nodegroup-name workers --node-type t3.medium --nodes 3
   ```

2. **Deploy with Helm** (recommended)
   ```bash
   # Create Helm chart
   helm create supplero-chart
   
   # Deploy
   helm install supplero ./supplero-chart
   ```

#### Google Cloud GKE Deployment

1. **Create GKE Cluster**
   ```bash
   gcloud container clusters create supplero-cluster \
     --zone us-central1-a \
     --num-nodes 3 \
     --machine-type e2-medium
   ```

2. **Deploy Application**
   ```bash
   # Get cluster credentials
   gcloud container clusters get-credentials supplero-cluster --zone us-central1-a
   
   # Deploy using kubectl
   kubectl apply -f kubernetes/
   ```

#### Azure AKS Deployment

1. **Create AKS Cluster**
   ```bash
   az aks create \
     --resource-group supplero-rg \
     --name supplero-cluster \
     --node-count 3 \
     --node-vm-size Standard_B2s
   ```

2. **Deploy Application**
   ```bash
   # Get credentials
   az aks get-credentials --resource-group supplero-rg --name supplero-cluster
   
   # Deploy
   kubectl apply -f kubernetes/
   ```

## Environment Configuration

### Development Environment
```bash
# .env for development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=dev_secret_key_change_in_production
```

### Production Environment
```bash
# .env for production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=very_secure_production_secret_key_here
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment (development/production) | Yes | development |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | - |
| `POSTGRES_DB` | Database name | Yes | supplero |
| `POSTGRES_USER` | Database user | Yes | supplero |
| `POSTGRES_PASSWORD` | Database password | Yes | - |
| `POSTGRES_HOST` | Database host | Yes | localhost |
| `REDIS_URL` | Redis connection URL | Yes | redis://localhost:6379 |
| `ELASTICSEARCH_URL` | Elasticsearch URL | Yes | http://localhost:9200 |
| `DUN_BRADSTREET_API_KEY` | D&B API key | No | - |
| `REFINITIV_API_KEY` | Refinitiv API key | No | - |
| `NEWS_API_KEY` | News API key | No | - |

## Security Considerations

### Production Security Checklist

- [ ] **Change Default Passwords**: Update all default passwords
- [ ] **Use Strong Secret Keys**: Generate cryptographically secure secret keys
- [ ] **Enable HTTPS**: Configure SSL/TLS certificates
- [ ] **Network Security**: Use proper firewall rules and network policies
- [ ] **Database Security**: Enable encryption at rest and in transit
- [ ] **API Security**: Implement rate limiting and authentication
- [ ] **Container Security**: Use non-root users and minimal base images
- [ ] **Secrets Management**: Use Kubernetes secrets or external secret management
- [ ] **Regular Updates**: Keep all dependencies and base images updated
- [ ] **Monitoring**: Implement security monitoring and alerting

### Security Best Practices

1. **Environment Variables**
   ```bash
   # Use strong, unique passwords
   POSTGRES_PASSWORD=$(openssl rand -base64 32)
   SECRET_KEY=$(openssl rand -base64 64)
   ```

2. **Kubernetes Security**
   ```yaml
   # Use security contexts
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     allowPrivilegeEscalation: false
     readOnlyRootFilesystem: true
   ```

3. **Network Policies**
   ```yaml
   # Restrict network access
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: supplero-network-policy
   spec:
     podSelector:
       matchLabels:
         app: backend
     policyTypes:
     - Ingress
     - Egress
   ```

## Monitoring and Maintenance

### Health Checks

1. **Application Health**
   ```bash
   # Backend health
   curl http://localhost:8000/health
   
   # Frontend health
   curl http://localhost:3000
   ```

2. **Database Health**
   ```bash
   # PostgreSQL
   docker exec supplero-postgres pg_isready -U supplero
   
   # Redis
   docker exec supplero-redis redis-cli ping
   ```

3. **Elasticsearch Health**
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

### Monitoring Setup

1. **Prometheus Metrics** (if enabled)
   ```yaml
   # Add to backend deployment
   - name: PROMETHEUS_ENABLED
     value: "true"
   ```

2. **Logging**
   ```bash
   # View application logs
   docker-compose logs -f backend
   docker-compose logs -f frontend
   
   # Kubernetes logs
   kubectl logs -f deployment/backend -n supplero
   kubectl logs -f deployment/frontend -n supplero
   ```

### Backup and Recovery

1. **Database Backup**
   ```bash
   # PostgreSQL backup
   docker exec supplero-postgres pg_dump -U supplero supplero > backup.sql
   
   # Restore
   docker exec -i supplero-postgres psql -U supplero supplero < backup.sql
   ```

2. **Volume Backups** (Kubernetes)
   ```bash
   # Create volume snapshots
   kubectl create -f volume-snapshot.yaml
   ```

## Troubleshooting

### Common Issues

1. **Services Won't Start**
   ```bash
   # Check logs
   docker-compose logs <service-name>
   
   # Check resource usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   docker exec supplero-postgres pg_isready -U supplero
   
   # Check connection logs
   docker logs supplero-postgres
   ```

3. **Frontend Build Issues**
   ```bash
   # Rebuild frontend
   docker-compose build frontend
   
   # Check Node.js version
   docker exec supplero-frontend node --version
   ```

4. **Kubernetes Issues**
   ```bash
   # Check pod status
   kubectl describe pod <pod-name> -n supplero
   
   # Check events
   kubectl get events -n supplero --sort-by='.lastTimestamp'
   
   # Check resource usage
   kubectl top pods -n supplero
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   # Adjust resource requests/limits
   resources:
     requests:
       memory: "512Mi"
       cpu: "500m"
     limits:
       memory: "1Gi"
       cpu: "1000m"
   ```

2. **Database Optimization**
   ```sql
   -- PostgreSQL tuning
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   ```

3. **Caching Strategy**
   ```python
   # Redis caching configuration
   CACHE_TTL = 3600  # 1 hour
   CACHE_PREFIX = "supplero:"
   ```

## Support and Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Health Endpoints**: http://localhost:8000/health
- **Logs**: Use `docker-compose logs` or `kubectl logs`
- **Issues**: Check the troubleshooting section above

---

**Happy Deploying! 🚀**

For additional support or questions, please refer to the project documentation or create an issue in the repository.
