import { NextRequest, NextResponse } from 'next/server';
import { buildApiUrl } from '@/lib/api-config';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    
    const backendUrl = buildApiUrl('/api/v1/documents/upload', true);
    
    // Debug logging
    const authHeader = request.headers.get('Authorization');
    console.log('Next.js Upload Route - Received headers:', {
      authorization: authHeader ? `${authHeader.substring(0, 20)}...` : 'none',
      'x-trace-id': request.headers.get('X-Trace-ID'),
      'x-correlation-id': request.headers.get('X-Correlation-ID'),
      'x-span-id': request.headers.get('X-Span-ID'),
    });
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': authHeader || '',
        'X-Trace-ID': request.headers.get('X-Trace-ID') || '',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') || '',
        'X-Span-ID': request.headers.get('X-Span-ID') || '',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend upload error:', response.status, errorData);
      throw new Error(`Backend responded with status: ${response.status}: ${errorData.detail || 'Unknown error'}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to upload document', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
