import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const backendUrl = buildApiUrl(`/api/v1/suppliers/${params.id}/risk`, true);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend supplier risk error:', response.status, errorData);
      return NextResponse.json(
        { error: 'Failed to fetch supplier risk', details: errorData.detail || 'Unknown error' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error (suppliers/:id/risk):', error);
    return NextResponse.json(
      { error: 'Failed to fetch supplier risk', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}


