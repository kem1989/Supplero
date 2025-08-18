import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const backendUrl = buildApiUrl('/api/v1/suppliers/profile', true);

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

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend supplier profile error:', response.status, errorData);
      return NextResponse.json(
        { error: 'Failed to create supplier profile', details: errorData.detail || 'Unknown error' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('API route error (suppliers/profile):', error);
    return NextResponse.json(
      { error: 'Failed to create supplier profile', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}


