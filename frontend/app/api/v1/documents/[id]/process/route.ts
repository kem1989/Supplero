import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const backendUrl = buildApiUrl(`/api/v1/documents/${params.id}/process`, true);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to process document' },
      { status: 500 }
    );
  }
}
