# 🚀 Supplero API Routing Guide

This guide explains the complete API routing architecture between the frontend and backend, and how to test it to ensure everything works correctly.

## 📋 Architecture Overview

### Frontend (Next.js)
- **Port**: 3000
- **URL**: http://localhost:3000
- **API Routes**: `/app/api/v1/*` (Next.js API routes that proxy to backend)

### Backend (FastAPI)
- **Port**: 8000
- **URL**: http://localhost:8000
- **API Base**: `/api/v1/*`
- **Documentation**: http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables

#### Frontend (.env.local or docker-compose.yml)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

#### Backend (.env)
```bash
API_PREFIX=/api/v1
ENVIRONMENT=development
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Docker Configuration

The `docker-compose.yml` ensures:
- Frontend uses `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Backend exposes port 8000
- Frontend exposes port 3000
- Both services are on the same Docker network

## 🌐 API Endpoint Structure

### Backend Endpoints
```
GET  /                    # Root endpoint
GET  /health             # Health check
GET  /docs               # API documentation
GET  /redoc              # Alternative API docs
GET  /api/v1/            # API v1 root
POST /api/v1/auth/login  # User login
POST /api/v1/auth/register # User registration
GET  /api/v1/auth/me     # Current user info
POST /api/v1/auth/refresh # Refresh token
GET  /api/v1/documents   # List documents
POST /api/v1/documents/upload # Upload document
GET  /api/v1/documents/{id} # Get document
POST /api/v1/documents/{id}/process # Process document
GET  /api/v1/organizations # List organizations
GET  /api/v1/audit       # Audit logs
POST /api/v1/audit-sink  # Audit sink
POST /api/v1/ai-assistant/query # Process natural language query
POST /api/v1/ai-assistant/execute # Execute AI tool
GET  /api/v1/ai-assistant/tools # Get available AI tools
POST /api/v1/ai-assistant/search-contracts # Search contracts with AI
```

### Frontend API Routes (Proxies)
```
POST /api/v1/auth/login  → POST http://localhost:8000/api/v1/auth/login
POST /api/v1/auth/register → POST http://localhost:8000/api/v1/auth/register
GET  /api/v1/auth/me     → GET http://localhost:8000/api/v1/auth/me
GET  /api/v1/documents   → GET http://localhost:8000/api/v1/documents
POST /api/v1/documents/upload → POST http://localhost:8000/api/v1/documents/upload
GET  /api/v1/documents/{id} → GET http://localhost:8000/api/v1/documents/{id}
POST /api/v1/documents/{id}/process → POST http://localhost:8000/api/v1/documents/{id}/process
POST /api/v1/ai-assistant/query → POST http://localhost:8000/api/v1/ai-assistant/query
POST /api/v1/ai-assistant/execute → POST http://localhost:8000/api/v1/ai-assistant/execute
GET  /api/v1/ai-assistant/tools → GET http://localhost:8000/api/v1/ai-assistant/tools
POST /api/v1/ai-assistant/search-contracts → POST http://localhost:8000/api/v1/ai-assistant/search-contracts
```

## 🧪 Testing the API Routing

### 1. Start the Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker logs supplero-frontend --tail 50
docker logs supplero-backend --tail 50
```

### 2. Run the Comprehensive Test Script
```bash
# Install requests if not available
pip install requests

# Run the test script
python test_api_routing.py
```

### 3. Manual Testing

#### Test Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"supplero-api","version":"1.0.0"}
```

#### Test Backend Root
```bash
curl http://localhost:8000/
# Expected: {"message":"Welcome to Supplero AI-Powered Procurement Platform","version":"1.0.0"}
```

#### Test API v1 Root
```bash
curl http://localhost:8000/api/v1/
# Expected: {"message":"Supplero API v1","version":"1.0.0","endpoints":{...}}
```

#### Test Authentication Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
# Expected: 422 (validation error) or 401 (unauthorized) - routing is working
```

#### Test Frontend Accessibility
```bash
curl http://localhost:3000
# Expected: 200 OK with HTML content
```

### 4. Browser Testing

1. Open http://localhost:3000 in your browser
2. Open browser developer tools (F12)
3. Go to Network tab
4. Try to login/register - you should see requests to `/api/v1/auth/*`
5. Check that requests are properly routed to the backend

## 🔍 Troubleshooting Common Issues

### Issue: "ERR_NAME_NOT_RESOLVED" for backend:8000
**Cause**: Frontend trying to use Docker internal hostname from browser
**Solution**: Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000` in environment

### Issue: CORS errors in browser
**Cause**: Backend not allowing frontend origin
**Solution**: Check `ALLOWED_ORIGINS` in backend config includes `http://localhost:3000`

### Issue: Frontend can't reach backend
**Cause**: Port conflicts or services not running
**Solution**: 
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000

# Restart services
docker-compose restart
```

### Issue: Environment variables not loading
**Cause**: `.env` file not properly configured
**Solution**: 
```bash
# Copy example environment
cp env.example .env

# Edit .env with your values
# Ensure NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 Understanding the Flow

### 1. Browser Request Flow
```
Browser → Frontend (localhost:3000) → Next.js API Route → Backend (localhost:8000)
```

### 2. Frontend API Route Example
```typescript
// frontend/app/api/v1/auth/login/route.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const backendUrl = `${BACKEND_URL}/api/v1/auth/login`;
  
  const response = await fetch(backendUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  
  return NextResponse.json(await response.json());
}
```

### 3. Backend Route Definition
```python
# backend/app/api/v1/auth.py
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    # Login logic here
    pass
```

### 4. API Router Inclusion
```python
# backend/app/api/v1/api.py
from .auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)

# backend/app/main.py
app.include_router(api_router, prefix=settings.API_PREFIX)
```

## 🎯 Best Practices

### 1. Environment Variables
- Always use `NEXT_PUBLIC_API_URL=http://localhost:8000` for development
- Never use Docker internal hostnames (`backend:8000`) in browser-accessible code
- Use `.env` files for configuration, not hardcoded values

### 2. Error Handling
- Frontend API routes should handle backend errors gracefully
- Return appropriate HTTP status codes
- Log errors for debugging

### 3. CORS Configuration
- Backend should allow frontend origin
- Use proper CORS middleware
- Test CORS with browser requests

### 4. Testing
- Run comprehensive tests after any routing changes
- Test both successful and error scenarios
- Verify CORS headers are properly set

## 🚀 Adding New Endpoints

### 1. Backend
```python
# backend/app/api/v1/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.get("/")
async def get_new_feature():
    return {"message": "New feature endpoint"}
```

### 2. Include in API Router
```python
# backend/app/api/v1/api.py
from .new_feature import router as new_feature_router

api_router.include_router(new_feature_router)
```

### 3. Frontend API Route (if needed)
```typescript
// frontend/app/api/v1/new-feature/route.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  const response = await fetch(`${BACKEND_URL}/api/v1/new-feature`);
  return NextResponse.json(await response.json());
}
```

### 4. Test the New Endpoint
```bash
# Test backend directly
curl http://localhost:8000/api/v1/new-feature

# Test frontend proxy (if created)
curl http://localhost:3000/api/v1/new-feature

# Run comprehensive tests
python test_api_routing.py
```

## 📝 Summary

Your Supplero application now has a robust API routing architecture:

✅ **Frontend**: Next.js API routes that proxy to backend  
✅ **Backend**: FastAPI with proper CORS and routing  
✅ **Environment**: Correctly configured for Docker development  
✅ **Testing**: Comprehensive test script to verify routing  
✅ **Documentation**: Clear guide for adding new features  

The routing is now consistent and will work reliably when you add new features. Always test new endpoints using the provided test script to ensure they're properly configured.
