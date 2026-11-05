import { getServerSession } from 'next-auth'
import { authOptions } from './authOptions'

export const businessUrl = (): string =>
  (process.env.BUSINESS_URL ?? 'http://backend:5000/api').replace(/\/$/, '')

export async function providerContext(
  request: Request,
  action: string,
): Promise<
  | { token: string; user: { id: number; email: string }; error?: never }
  | { error: Response; token?: never; user?: never }
> {
  const bearer = request.headers.get('Authorization')
  const session = bearer ? null : await getServerSession(authOptions)
  const token =
    bearer ?? (session?.accessToken ? `Bearer ${session.accessToken}` : '')
  if (!token.startsWith('Bearer ')) {
    return {
      error: Response.json(
        { error: 'Authentication required' },
        { status: 401 },
      ),
    }
  }
  try {
    const response = await fetch(`${businessUrl()}/provider/authorize`, {
      method: 'POST',
      headers: { Authorization: token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
      cache: 'no-store',
      signal: AbortSignal.timeout(5000),
    })
    if (!response.ok) {
      return {
        error: Response.json(
          { error: 'Provider authorization rejected' },
          { status: response.status },
        ),
      }
    }
    const data = await response.json()
    return { token, user: data.user }
  } catch {
    return {
      error: Response.json(
        { error: 'Authorization unavailable' },
        { status: 503 },
      ),
    }
  }
}

export async function queueLocalEmail(
  request: Request,
  kind: string,
): Promise<Response> {
  const context = await providerContext(request, 'email')
  if (context.error) return context.error
  try {
    const body = await request.json()
    const response = await fetch(`${businessUrl()}/email/${kind}`, {
      method: 'POST',
      headers: {
        Authorization: context.token,
        'Content-Type': 'application/json',
        'X-Correlation-ID': request.headers.get('X-Correlation-ID') ?? '',
        'X-Operation-ID': request.headers.get('X-Operation-ID') ?? '',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(8000),
    })
    return Response.json(await response.json(), { status: response.status })
  } catch {
    return Response.json(
      { error: 'Mail unavailable or invalid body' },
      { status: 503 },
    )
  }
}
