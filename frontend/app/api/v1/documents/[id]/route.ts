import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const backendUrl = buildApiUrl(`/api/v1/documents/${params.id}`, true);
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
      { error: 'Failed to fetch document' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const backendUrl = buildApiUrl(`/api/v1/documents/${params.id}`, true);
    
    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'X-Trace-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to delete document' },
      { status: 500 }
    );
  }
}
