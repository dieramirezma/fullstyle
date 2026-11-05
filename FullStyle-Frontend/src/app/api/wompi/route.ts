import { providerContext } from '@/utils/providerBoundary'

export async function POST(request: Request): Promise<Response> {
  const context = await providerContext(request, 'payment')
  if (context.error) return context.error
  return Response.json(
    { error: 'External provider disabled in local environment', mode: 'local' },
    { status: 503 },
  )
}
