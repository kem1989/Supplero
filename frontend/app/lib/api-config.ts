/**
 * API Configuration Utility
 * 
 * This utility provides the correct API URL based on the context:
 * - NEXT_PUBLIC_API_URL: Used for client-side requests (browser)
 * - INTERNAL_API_URL: Used for server-side requests (Next.js API routes)
 */

// For client-side requests (browser)
export const CLIENT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// For server-side requests (Next.js API routes)
export const SERVER_API_URL = process.env.INTERNAL_API_URL || 'http://backend:8000';

/**
 * Get the appropriate API URL based on context
 * @param isServerSide - Whether this is a server-side request
 * @returns The appropriate API URL
 */
export function getApiUrl(isServerSide: boolean = false): string {
  return isServerSide ? SERVER_API_URL : CLIENT_API_URL;
}

/**
 * Build a complete API endpoint URL
 * @param endpoint - The API endpoint path (e.g., '/api/v1/auth/login')
 * @param isServerSide - Whether this is a server-side request
 * @returns The complete API URL
 */
export function buildApiUrl(endpoint: string, isServerSide: boolean = false): string {
  const baseUrl = getApiUrl(isServerSide);
  // Ensure endpoint starts with / and remove any duplicate slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}



