"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "supplero-api"
        assert "version" in data
        assert "environment" in data
    
    def test_health_live(self):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    @patch('app.api.health.get_db')
    @patch('app.api.health.get_redis')
    @patch('httpx.AsyncClient')
    def test_health_ready_success(self, mock_client, mock_redis, mock_db):
        """Test readiness check when all services are healthy."""
        # Mock database
        mock_db_session = MagicMock()
        mock_db_session.execute.return_value = None
        mock_db.return_value = mock_db_session
        
        # Mock Redis
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        # Mock Elasticsearch
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    def test_api_root(self):
        """Test API root endpoint."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Supplero API v1"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data 