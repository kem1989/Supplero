import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const backendUrl = buildApiUrl('/api/v1/ai-assistant/query', true);
    
    // Debug logging
    console.log('Next.js AI Assistant Query Route - Request body:', body);
    console.log('Next.js AI Assistant Query Route - Backend URL:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
      body: JSON.stringify(body),
    });

    console.log('Next.js AI Assistant Query Route - Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend AI assistant query error:', response.status, errorData);
      throw new Error(`Backend responded with status: ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data = await response.json();
    console.log('Next.js AI Assistant Query Route - Response data:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to process AI assistant query', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
