import { verifyEvent, eventCapability } from '@/utils/wompiEvent'
import { businessUrl } from '@/utils/providerBoundary'

export const runtime = 'nodejs'

export async function POST(request: Request): Promise<Response> {
  const checksum = request.headers.get('X-Event-Checksum') ?? ''
  if (!checksum)
    return Response.json(
      { error: 'Missing required signature header' },
      { status: 400 },
    )
  if (Number(request.headers.get('content-length') ?? 0) > 65536)
    return Response.json({ error: 'Event too large' }, { status: 413 })
  let body
  try {
    body = await request.json()
  } catch {
    return Response.json({ error: 'Invalid JSON' }, { status: 400 })
  }
  const eventSecret = process.env.WOMPI_EVENTS_KEY ?? ''
  const serviceSecret = process.env.INTEGRATION_SECRET ?? ''
  if (!eventSecret || !serviceSecret)
    return Response.json(
      { error: 'Event adapter unavailable' },
      { status: 503 },
    )
  if (!verifyEvent(body, checksum, eventSecret))
    return Response.json({ error: 'Invalid signature' }, { status: 401 })
  try {
    const response = await fetch(`${businessUrl()}/integrations/wompi/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${eventCapability(body, serviceSecret)}`,
        'X-Event-Checksum': checksum,
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') ?? '',
        'X-Operation-ID': request.headers.get('X-Operation-ID') ?? '',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    })
    return Response.json(await response.json(), { status: response.status })
  } catch {
    return Response.json(
      { error: 'Event persistence unavailable' },
      { status: 503 },
    )
  }
}
