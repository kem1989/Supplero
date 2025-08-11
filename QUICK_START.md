# 🚀 Supplero Quick Start Guide

Quick commands to get your Supplero development environment up and running.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for local development if needed)
- Python 3.11+ (for local development if needed)

## 🚀 Start Development Environment

### **Option 1: Start All Services (Recommended)**
```bash
# Start all services in the background
docker-compose up -d

# Check status of all services
docker-compose ps
```

### **Option 2: Start Services with Logs**
```bash
# Start all services and see logs in real-time
docker-compose up

# Or start specific service with logs
docker-compose up frontend
```

## 🔍 Check Service Status

```bash
# View all running containers
docker-compose ps

# Check specific service logs
docker logs supplero-frontend --tail 50
docker logs supplero-backend --tail 50
docker logs supplero-postgres --tail 20
```

## 🌐 Access Your Services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React/Next.js application with Tailwind CSS |
| **Backend API** | http://localhost:8000 | FastAPI backend with health endpoint |
| **PostgreSQL** | localhost:5432 | Database (user: `supplero`, password: `supplero_dev`) |
| **Redis** | localhost:6379 | Cache and session storage |
| **Elasticsearch** | http://localhost:9200 | Search and analytics engine |

## 🧪 Test Your Services

### **Test Frontend**
```bash
# Check if frontend is responding
curl http://localhost:3000 | grep "Welcome to Supplero"
```

### **Test Backend API**
```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"supplero-api","version":"1.0.0","environment":"development"}
```

### **Test Database**
```bash
# Test PostgreSQL connection
docker exec supplero-postgres psql -U supplero -d supplero -c "SELECT version();"
```

### **Test Redis**
```bash
# Test Redis connection
docker exec supplero-redis redis-cli ping
# Expected response: PONG
```

### **Test Elasticsearch**
```bash
# Check cluster health
curl http://localhost:9200/_cluster/health
# Expected: {"status":"green",...}
```

## 🛑 Stop Development Environment

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ This will delete all data!)
docker-compose down -v
```

## 🔄 Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart frontend
docker-compose restart backend
```

## 🏗️ Rebuild Services (After Code Changes)

```bash
# Rebuild specific service
docker-compose build frontend
docker-compose build backend

# Rebuild and start
docker-compose up --build frontend
```

## 📁 Development Workflow

1. **Start services**: `docker-compose up -d`
2. **Make code changes** in your local files
3. **Services auto-reload** thanks to volume mounts
4. **View logs**: `docker logs <service-name> --tail 50`
5. **Stop when done**: `docker-compose down`

## 🐛 Troubleshooting

### **Service Won't Start**
```bash
# Check logs
docker logs <service-name>

# Check container status
docker-compose ps

# Restart service
docker-compose restart <service-name>
```

### **Database Connection Issues**
```bash
# Check PostgreSQL logs
docker logs supplero-postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### **Frontend Styling Issues**
```bash
# Rebuild frontend container
docker-compose build frontend
docker-compose up -d frontend
```

### **Port Already in Use**
```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

## 📚 Useful Commands

```bash
# View all containers (including stopped ones)
docker ps -a

# View resource usage
docker stats

# Clean up unused containers/images
docker system prune

# View service dependencies
docker-compose config
```

## 🎯 Quick Commands Summary

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker logs supplero-frontend --tail 50

# Stop everything
docker-compose down
```

---

**Happy coding! 🎉**

Your Supplero development environment is ready to go with AI-powered procurement and supplier risk management features. 