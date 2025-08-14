import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const backendUrl = buildApiUrl('/api/v1/auth/register', true);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend register error:', response.status, errorData);
      throw new Error(`Backend responded with status: ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to register', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
