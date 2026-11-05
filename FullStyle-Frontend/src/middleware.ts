import { getToken } from 'next-auth/jwt'
import { type NextRequest, NextResponse } from 'next/server'

export async function middleware(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET })

  const { pathname } = req.nextUrl
  // api/subscription

  // Si no hay token, redirige al login
  if (token == null) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  try {
    const response = await fetch(
      `${process.env.BUSINESS_URL ?? 'http://backend:5000/api'}/me`,
      {
        headers: { Authorization: `Bearer ${String(token.accessToken ?? '')}` },
        cache: 'no-store',
        signal: AbortSignal.timeout(5000),
      },
    )
    if (!response.ok) return NextResponse.redirect(new URL('/login', req.url))
    const identity = await response.json()
    token.is_manager = identity.is_manager
    token.subscriptionactive = identity.subscriptionactive
  } catch {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (pathname.startsWith('/owner') && token.subscriptionactive === false) {
    return NextResponse.redirect(new URL('/plans', req.url))
  } else if (token.subscriptionactive && pathname.startsWith('/plans')) {
    return NextResponse.redirect(new URL('/owner', req.url))
  }

  if (pathname.startsWith('/plans') && token.subscriptionactive === true) {
    return NextResponse.redirect(new URL('/owner', req.url))
  }

  if (
    (pathname.startsWith('/owner') || pathname.startsWith('/plans')) &&
    !token.is_manager
  ) {
    return NextResponse.redirect(new URL('/customer', req.url))
  }

  if (pathname.startsWith('/customer') && token.is_manager) {
    return NextResponse.redirect(new URL('/owner', req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/customer/:path*', '/owner/:path*', '/plans/:path*'],
}
