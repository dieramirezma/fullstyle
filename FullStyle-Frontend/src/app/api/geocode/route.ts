import { providerContext } from '@/utils/providerBoundary'

export async function GET(request: Request): Promise<Response> {
  const context = await providerContext(request, 'geocode')
  if (context.error) return context.error
  return Response.json(
    { error: 'External provider disabled in local environment', mode: 'local' },
    { status: 503 },
  )
}
