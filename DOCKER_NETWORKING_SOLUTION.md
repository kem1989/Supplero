# 🐳 Docker Networking Solution for Supplero

## 🚨 Problem Description

The application had a fundamental architectural issue with Docker networking:

1. **Frontend container** runs on port 3000 (accessible from host as `localhost:3000`)
2. **Backend container** runs on port 8000 (accessible from host as `localhost:8000`)
3. **Browser** makes requests to `localhost:3000`
4. **Frontend API routes** need to reach the backend

**The Problem**: When the browser makes a request to `/api/v1/auth/login`, the frontend container receives it and tries to forward it to the backend. But the frontend container can't reach `localhost:8000` because that refers to itself, not the host machine.

## ✅ Solution Implemented

### 1. **Dual Environment Variables in Docker Compose**

Updated `docker-compose.yml` to have both URLs:

```yaml
environment:
  - NEXT_PUBLIC_API_URL=http://localhost:8000  # For browser requests
  - INTERNAL_API_URL=http://backend:8000        # For server-side requests
```

### 2. **API Configuration Utility**

Created `frontend/app/lib/api-config.ts` to handle URL selection:

```typescript
// For client-side requests (browser)
export const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// For server-side requests (Next.js API routes)
export const SERVER_API_URL = process.env.INTERNAL_API_URL || 'http://backend:8000';

export function getApiUrl(isServerSide: boolean = false): string {
  return isServerSide ? SERVER_API_URL : CLIENT_API_URL;
}

export function buildApiUrl(endpoint: string, isServerSide: boolean = false): string {
  const baseUrl = getApiUrl(isServerSide);
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}
```

### 3. **Updated Next.js API Routes**

All Next.js API routes now use the server-side URL:

```typescript
import { buildApiUrl } from '@/lib/api-config';

export async function POST(request: NextRequest) {
  try {
    const backendUrl = buildApiUrl('/api/v1/auth/login', true); // true = server-side
    const response = await fetch(backendUrl, {
      // ... request configuration
    });
    // ... response handling
  } catch (error) {
    // ... error handling
  }
}
```

### 4. **Fixed Frontend API Base URL**

Updated `frontend/app/lib/auth.ts` to use correct base URL:

```typescript
// Before: baseURL: '/api' (caused double /api paths)
// After: baseURL: '/api/v1' (correct path structure)

const API_BASE_URL = '/api/v1';
```

### 5. **Updated Component API Calls**

Components now call endpoints without the `/api/v1` prefix:

```typescript
// Before: api.post('/api/v1/ai-assistant/search-contracts', ...)
// After: api.post('/ai-assistant/search-contracts', ...)

const response = await api.post('/ai-assistant/search-contracts', {
  query: query.trim(),
  user_context: null
});
```

## 🔄 How It Works Now

### **Request Flow:**

1. **Browser** → `localhost:3000/api/v1/auth/login`
2. **Next.js** receives request at `/api/v1/auth/login`
3. **Next.js API Route** uses `INTERNAL_API_URL=http://backend:8000`
4. **Next.js** forwards request to `http://backend:8000/api/v1/auth/login`
5. **Backend** processes request and returns response
6. **Next.js** forwards response back to browser

### **URL Resolution:**

- **Client-side requests**: Use `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Server-side requests**: Use `INTERNAL_API_URL=http://backend:8000`

## 🧪 Testing the Solution

### **1. Restart Docker Services**

```bash
# Stop all services
docker-compose down

# Start services with new configuration
docker-compose up --build
```

### **2. Verify Environment Variables**

```bash
# Check frontend environment
docker exec supplero-frontend env | grep -E "(NEXT_PUBLIC_API_URL|INTERNAL_API_URL)"

# Expected output:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# INTERNAL_API_URL=http://backend:8000
```

### **3. Test API Endpoints**

```bash
# Test frontend API route (should proxy to backend)
curl http://localhost:3000/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Test backend directly
curl http://localhost:8000/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

### **4. Check Container Logs**

```bash
# Frontend logs
docker logs supplero-frontend --tail 20

# Backend logs
docker logs supplero-backend --tail 20
```

## 🎯 Benefits of This Solution

1. **Eliminates Docker networking issues** - Server-side requests use Docker service names
2. **Maintains browser compatibility** - Client-side requests use host URLs
3. **Centralized configuration** - Single source of truth for API URLs
4. **Easy to maintain** - Clear separation of concerns
5. **Scalable** - Easy to add more services or change URLs

## 🔧 Troubleshooting

### **Common Issues:**

1. **Environment variables not set**: Restart Docker containers
2. **API routes returning 500**: Check backend logs for connection errors
3. **CORS issues**: Verify backend CORS configuration includes `localhost:3000`

### **Debug Commands:**

```bash
# Test container connectivity
docker exec supplero-frontend ping backend
docker exec supplero-frontend curl http://backend:8000/health

# Check network configuration
docker network ls
docker network inspect supplero_supplero-network
```

## 📚 Related Files Modified

- `docker-compose.yml` - Added dual environment variables
- `frontend/app/lib/api-config.ts` - New utility file
- `frontend/app/lib/auth.ts` - Fixed API base URL
- All Next.js API routes - Updated to use server-side URLs
- Frontend components - Updated API calls to remove `/api/v1` prefix

## 🚀 Next Steps

1. **Test the solution** with the commands above
2. **Monitor logs** for any remaining issues
3. **Update documentation** if needed
4. **Consider adding health checks** for better monitoring

This solution provides a robust, maintainable architecture that properly separates client-side and server-side API communication while maintaining Docker networking best practices.



