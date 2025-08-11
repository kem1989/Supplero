#!/bin/bash

# Supplero Development Environment Setup Script
# This script sets up the development environment for the Supplero project

set -e

echo "🚀 Setting up Supplero Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your OpenAI API key and other configurations"
    echo "   Then run this script again."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY is not set in .env file"
    echo "   Please add your OpenAI API key to the .env file"
    exit 1
fi

echo "✅ Environment variables configured"

# Build and start services
echo "🔨 Building Docker images..."
make build

echo "🚀 Starting services..."
make up

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔍 Checking service health..."
make health

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📱 Access your services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   Elasticsearch: http://localhost:9200"
echo ""
echo "🛠️  Useful commands:"
echo "   make logs      - View service logs"
echo "   make down      - Stop services"
echo "   make restart   - Restart services"
echo "   make test      - Run tests"
echo "   make lint      - Run linting"
echo "   make format    - Format code"
echo ""
echo "📚 For more information, see README.md"
echo "" 