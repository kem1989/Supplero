import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import Cookies from 'js-cookie';
import { 
  addTraceHeadersToRequest, 
  handleTraceResponse, 
  getCurrentTraceContext,
  logTraceInfo 
} from './tracing';

// API base URL - Use Next.js API routes for client-side requests
const API_BASE_URL = '/api/v1';

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
export const TOKEN_KEY = 'supplero_access_token';
export const REFRESH_TOKEN_KEY = 'supplero_refresh_token';

export interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  organization_id: number;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
  organization_id: number;
  role?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Token utilities
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return Cookies.get(TOKEN_KEY) || null;
};

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return Cookies.get(REFRESH_TOKEN_KEY) || null;
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  Cookies.set(TOKEN_KEY, accessToken, { expires: 1/24 }); // 1 hour
  Cookies.set(REFRESH_TOKEN_KEY, refreshToken, { expires: 7 }); // 7 days
};

export const clearTokens = (): void => {
  Cookies.remove(TOKEN_KEY);
  Cookies.remove(REFRESH_TOKEN_KEY);
};

export const isTokenValid = (token: string): boolean => {
  try {
    const decoded = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp ? decoded.exp > currentTime : false;
  } catch {
    return false;
  }
};

// API request interceptor to add auth token and trace headers
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add trace headers
    config = addTraceHeadersToRequest(config);
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API response interceptor to handle trace information
api.interceptors.response.use(
  (response) => {
    // Handle trace information from response
    response = handleTraceResponse(response);
    return response;
  },
  (error) => {
    // Log trace info for errors too
    if (error.response) {
      const traceInfo = {
        ...getCurrentTraceContext(),
        error: error.message,
        status: error.response.status
      };
      logTraceInfo('API Error', traceInfo);
    }
    return Promise.reject(error);
  }
);

// Authentication API functions
export const authAPI = {
  // Login user
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const traceContext = getCurrentTraceContext();
    logTraceInfo('Login Request', traceContext);
    
    console.log('authAPI: Making login request to:', '/auth/login');
    console.log('authAPI: Credentials:', credentials);
    console.log('authAPI: Trace Context:', traceContext);
    
    const response = await api.post('/auth/login', credentials);
    console.log('authAPI: Login response received:', response.data);
    
    const { access_token, refresh_token } = response.data;
    setTokens(access_token, refresh_token);
    console.log('authAPI: Tokens set successfully');
    
    // Log successful login with trace info
    logTraceInfo('Login Success', {
      ...traceContext,
      userId: response.data.user.id,
      userEmail: response.data.user.email
    });
    
    return response.data;
  },

  // Register user
  async register(userData: RegisterData): Promise<User> {
    const traceContext = getCurrentTraceContext();
    logTraceInfo('Register Request', traceContext);
    
    const response = await api.post('/auth/register', userData);
    
    // Log successful registration with trace info
    logTraceInfo('Register Success', {
      ...traceContext,
      userEmail: userData.email,
      username: userData.username
    });
    
    return response.data;
  },

  // Get current user info
  async getCurrentUser(): Promise<User> {
    const traceContext = getCurrentTraceContext();
    logTraceInfo('Get Current User', traceContext);
    
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Logout user
  async logout(): Promise<void> {
    const traceContext = getCurrentTraceContext();
    logTraceInfo('Logout Request', traceContext);
    
    clearTokens();
    
    // Log successful logout with trace info
    logTraceInfo('Logout Success', traceContext);
  },
};

// Check if user is authenticated
export const isAuthenticated = (): boolean => {
  const token = getToken();
  return token ? isTokenValid(token) : false;
}; 