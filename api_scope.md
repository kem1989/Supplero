# 🔧 API Error Correction Guide - Supplero Platform

## Overview
This document provides a comprehensive guide for resolving common API-related errors encountered during frontend-backend integration in the Supplero platform, particularly when working with Docker containers.

---

## 🚨 Common API Errors & Solutions

### 1. **ERR_NAME_NOT_RESOLVED - Docker Networking Issues**

**Error Message:**
```
GET http://backend:8000/api/v1/documents/ net::ERR_NAME_NOT_RESOLVED
```

**Root Cause:**
- Frontend (browser) trying to resolve `backend:8000` hostname
- `backend` is only valid within Docker network, not from browser
- Next.js rewrite rules not working properly

**Solutions:**

#### **Option A: Fix Next.js Rewrite Configuration**
```javascript
// frontend/next.config.js
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'}/api/v1/:path*`,
    },
  ]
}
```

**Key Points:**
- Use `http://backend:8000` (Docker service name) not `127.0.0.1:8000`
- Ensure `NEXT_PUBLIC_API_URL` environment variable is set correctly
- Restart frontend container after config changes

#### **Option B: Create Next.js API Routes (Recommended)**
```typescript
// frontend/app/api/v1/documents/route.ts
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/api/v1/documents`;
    const response = await fetch(backendUrl, {
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        // ... other headers
      },
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch documents' }, { status: 500 });
  }
}
```

**Benefits:**
- Server-side proxying eliminates Docker networking issues
- Better error handling and logging
- More reliable than rewrites

---

### 2. **404 Not Found - API Endpoint Mismatch**

**Error Message:**
```
Request failed with status code 404
```

**Root Causes:**
- Double path segments (e.g., `/api/v1/v1/documents`)
- Incorrect API endpoint paths
- Backend router not properly registered

**Solutions:**

#### **Check API Call Paths**
```typescript
// ❌ Wrong - causes double v1
const response = await api.get('/v1/documents');

// ✅ Correct - single path
const response = await api.get('/documents');
```

#### **Verify Backend Router Registration**
```python
# backend/app/api/v1/api.py
from .documents import router as documents_router

api_router.include_router(documents_router)

# backend/app/main.py
app.include_router(api_router, prefix=settings.API_PREFIX)
```

#### **Check Backend Endpoint Structure**
```python
# backend/app/api/v1/documents.py
router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/", response_model=DocumentListResponse)  # ✅ Correct
async def list_documents():
    # ... implementation
```

---

### 3. **Authentication & Authorization Errors**

**Error Message:**
```
{"detail":"Not authenticated"}
```

**Solutions:**

#### **Verify Token in Frontend**
```typescript
// frontend/app/lib/auth.ts
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### **Check Backend Auth Middleware**
```python
# backend/app/api/v1/documents.py
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user)  # ✅ Auth dependency
):
    # ... implementation
```

---

## 🏗️ **Recommended Architecture Pattern**

### **Frontend API Calls**
```typescript
// ✅ Use relative paths that match Next.js API routes
const response = await api.get('/v1/documents');
const response = await api.post('/v1/documents/upload', formData);
const response = await api.get(`/v1/documents/${documentId}`);
```

### **Next.js API Route Structure**
```
frontend/app/api/v1/
├── documents/
│   ├── route.ts                    # GET /api/v1/documents
│   ├── [id]/
│   │   ├── route.ts               # GET/DELETE /api/v1/documents/[id]
│   │   └── process/
│   │       └── route.ts           # POST /api/v1/documents/[id]/process
│   └── upload/
│       └── route.ts               # POST /api/v1/documents/upload
```

### **Backend API Structure**
```
backend/app/api/v1/
├── documents.py                    # /api/v1/documents endpoints
├── auth.py                        # /api/v1/auth endpoints
└── api.py                         # Router registration
```

---

## 🔍 **Debugging Checklist**

### **When API Calls Fail:**

1. **Check Docker Container Status**
   ```bash
   docker-compose ps
   docker logs supplero-frontend --tail 20
   docker logs supplero-backend --tail 20
   ```

2. **Verify Network Connectivity**
   ```bash
   docker exec supplero-frontend ping backend
   docker exec supplero-frontend curl http://backend:8000/health
   ```

3. **Check API Endpoint Registration**
   ```bash
   curl http://localhost:8000/docs  # Swagger UI
   curl http://localhost:8000/openapi.json | jq '.paths'
   ```

4. **Verify Frontend API Configuration**
   ```typescript
   // Check base URL and interceptors
   console.log('API Base URL:', api.defaults.baseURL);
   console.log('Request Headers:', config.headers);
   ```

5. **Test Next.js API Routes**
   ```bash
   # Test if API route is working
   curl http://localhost:3000/api/v1/documents
   ```

---

## 🚀 **Quick Fix Commands**

### **Restart Services**
```bash
# Restart specific service
docker-compose restart frontend
docker-compose restart backend

# Restart all services
docker-compose restart
```

### **Rebuild Services**
```bash
# Rebuild and restart
docker-compose up --build frontend
docker-compose up --build backend
```

### **Check Environment Variables**
```bash
# Check frontend environment
docker exec supplero-frontend env | grep NEXT_PUBLIC

# Check backend environment
docker exec supplero-backend env | grep API
```

---

## 📚 **Best Practices**

### **1. Always Use Next.js API Routes for Backend Communication**
- Eliminates CORS issues
- Provides server-side error handling
- Better security and logging

### **2. Consistent API Path Structure**
- Frontend: `/api/v1/documents`
- Next.js Route: `/app/api/v1/documents/route.ts`
- Backend: `/api/v1/documents`

### **3. Proper Error Handling**
```typescript
try {
  const response = await api.get('/v1/documents');
  // Handle success
} catch (error: any) {
  console.error('API Error:', error);
  if (error.response?.status === 404) {
    // Handle 404
  } else if (error.code === 'ERR_NETWORK') {
    // Handle network errors
  }
}
```

### **4. Environment Variable Management**
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://backend:8000

# docker-compose.yml
environment:
  - NEXT_PUBLIC_API_URL=http://backend:8000
```

---

## 🎯 **Common Scenarios & Solutions**

### **Scenario 1: New API Endpoint Not Working**
1. Check backend router registration
2. Verify endpoint path in backend
3. Create corresponding Next.js API route
4. Update frontend API calls
5. Restart containers

### **Scenario 2: Authentication Failing**
1. Check token storage and retrieval
2. Verify backend auth middleware
3. Check request headers in interceptors
4. Test with Postman/curl first

### **Scenario 3: File Upload Issues**
1. Check file size limits
2. Verify multipart/form-data handling
3. Check backend file processing pipeline
4. Ensure proper error handling

---

## 🔧 **Troubleshooting Commands Reference**

```bash
# Check container status
docker-compose ps

# View logs
docker logs supplero-frontend --tail 50
docker logs supplero-backend --tail 50

# Execute commands in containers
docker exec supplero-frontend npm run type-check
docker exec supplero-backend python -c "import app; print('Backend OK')"

# Check network connectivity
docker exec supplero-frontend ping backend
docker exec supplero-frontend curl -s http://backend:8000/health

# Restart services
docker-compose restart frontend
docker-compose restart backend

# Rebuild services
docker-compose up --build
```

---

## 📝 **Documentation Updates**

**When adding new API endpoints:**
1. Update this guide with new error patterns
2. Document the complete API flow
3. Add troubleshooting steps for new features
4. Update the debugging checklist

---

**Last Updated:** 2025-08-14  
**Version:** 1.0  
**Maintained By:** Development Team

