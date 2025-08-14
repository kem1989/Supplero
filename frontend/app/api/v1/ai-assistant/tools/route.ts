import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = buildApiUrl('/api/v1/ai-assistant/tools', true);
    
    // Debug logging
    console.log('Next.js AI Assistant Tools Route - Backend URL:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
    });

    console.log('Next.js AI Assistant Tools Route - Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend AI assistant tools error:', response.status, errorData);
      throw new Error(`Backend responded with status: ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data = await response.json();
    console.log('Next.js AI Assistant Tools Route - Response data:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch AI assistant tools', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
