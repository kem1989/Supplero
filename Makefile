# Supplero Development Environment Makefile

.PHONY: help build up down logs clean test lint format docker-build docker-push k8s-deploy k8s-delete

# Default target
help:
	@echo "Supplero Development Environment Commands:"
	@echo ""
	@echo "Local Development (Docker Compose):"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - View logs from all services"
	@echo "  clean     - Remove all containers, volumes, and images"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test      - Run all tests"
	@echo "  lint      - Run linting checks"
	@echo "  format    - Format code"
	@echo ""
	@echo "Docker Operations:"
	@echo "  docker-build - Build production Docker images"
	@echo "  docker-push  - Push images to registry"
	@echo ""
	@echo "Kubernetes:"
	@echo "  k8s-deploy - Deploy to Kubernetes"
	@echo "  k8s-delete - Delete from Kubernetes"

# Local Development
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all
	docker system prune -f

# Testing & Quality
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html
	@echo "Running frontend tests..."
	cd frontend && npm test

lint:
	@echo "Linting backend..."
	cd backend && flake8 app/ tests/ && mypy app/
	@echo "Linting frontend..."
	cd frontend && npm run lint

format:
	@echo "Formatting backend..."
	cd backend && black app/ tests/ && isort app/ tests/
	@echo "Formatting frontend..."
	cd frontend && npm run format

# Docker Operations
docker-build:
	@echo "Building production images..."
	docker build -f backend/Dockerfile -t ghcr.io/supplero/backend:latest ./backend
	docker build -f frontend/Dockerfile -t ghcr.io/supplero/frontend:latest ./frontend

docker-push:
	@echo "Pushing images to registry..."
	docker push ghcr.io/supplero/backend:latest
	docker push ghcr.io/supplero/frontend:latest

# Kubernetes
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f kubernetes/namespaces.yaml
	kubectl apply -f kubernetes/postgres.yaml
	kubectl apply -f kubernetes/redis.yaml
	kubectl apply -f kubernetes/elasticsearch.yaml
	kubectl apply -f kubernetes/backend.yaml
	kubectl apply -f kubernetes/frontend.yaml
	@echo "Waiting for deployments to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment/postgres -n supplero
	kubectl wait --for=condition=available --timeout=300s deployment/redis -n supplero
	kubectl wait --for=condition=available --timeout=300s deployment/elasticsearch -n supplero
	kubectl wait --for=condition=available --timeout=300s deployment/backend -n supplero
	kubectl wait --for=condition=available --timeout=300s deployment/frontend -n supplero

k8s-delete:
	@echo "Deleting from Kubernetes..."
	kubectl delete -f kubernetes/frontend.yaml --ignore-not-found=true
	kubectl delete -f kubernetes/backend.yaml --ignore-not-found=true
	kubectl delete -f kubernetes/elasticsearch.yaml --ignore-not-found=true
	kubectl delete -f kubernetes/redis.yaml --ignore-not-found=true
	kubectl delete -f kubernetes/postgres.yaml --ignore-not-found=true
	kubectl delete -f kubernetes/namespaces.yaml --ignore-not-found=true

# Database operations
db-init:
	@echo "Initializing database..."
	docker-compose exec postgres psql -U supplero -d supplero -f /docker-entrypoint-initdb.d/init-db.sql

db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres
	sleep 10
	make db-init

# Health checks
health:
	@echo "Checking service health..."
	@echo "Backend: $(shell curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "unavailable")"
	@echo "Frontend: $(shell curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "unavailable")"
	@echo "PostgreSQL: $(shell docker-compose exec -T postgres pg_isready -U supplero > /dev/null 2>&1 && echo "healthy" || echo "unhealthy")"
	@echo "Redis: $(shell docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo "healthy" || echo "unhealthy")"
	@echo "Elasticsearch: $(shell curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/_cluster/health || echo "unavailable")"

# Development shortcuts
dev: build up
	@echo "Development environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"
	@echo "Elasticsearch: http://localhost:9200"

restart:
	docker-compose restart

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-postgres:
	docker-compose exec postgres psql -U supplero -d supplero 