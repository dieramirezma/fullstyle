import { type NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import { createHmac } from 'node:crypto'

const backend = (): string =>
  (process.env.BUSINESS_URL ?? 'http://backend:5000/api').replace(/\/$/, '')

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Correo', type: 'email' },
        password: { label: 'Contraseña', type: 'password' },
        otp: { label: 'Código de autenticación', type: 'text' },
      },
      async authorize(credentials) {
        const response = await fetch(
          process.env.INTERNAL_GRAPHQL_URL ?? 'http://gateway:4000/',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query:
                'mutation Login($email:String!,$password:String!,$otp:String){login(email:$email,password:$password,otp:$otp){token refresh_token user{id name email active}}}',
              variables: {
                email: credentials?.email,
                password: credentials?.password,
                otp: credentials?.otp,
              },
            }),
            signal: AbortSignal.timeout(8000),
          },
        )
        const result = await response.json()
        const login = result?.data?.login
        if (!response.ok || !login?.token || !login?.user?.active) return null
        // Resolve authorization attributes from business, never defaults or client input.
        const identity = await fetch(`${backend()}/me`, {
          headers: { Authorization: `Bearer ${login.token}` },
          signal: AbortSignal.timeout(5000),
          cache: 'no-store',
        })
        if (!identity.ok) return null
        const user = await identity.json()
        return {
          ...user,
          token: login.token,
          refreshToken: login.refresh_token,
        }
      },
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: 'jwt', maxAge: 30 * 24 * 60 * 60 },
  pages: { signIn: '/login', error: '/login' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.token
        token.refreshToken = user.refreshToken
        token.user = user
        token.id = user.id
        token.is_manager = user.is_manager
        token.subscriptionactive = user.subscriptionactive
      }
      // Compact both new and legacy cookies; credentials belong only at the top level.
      if (token.user && typeof token.user === 'object') {
        const identity = { ...(token.user as Record<string, unknown>) }
        delete identity.token
        delete identity.refreshToken
        token.user = identity
      }
      const access = token.accessToken as string | undefined
      if (!access) return token
      try {
        const claims = JSON.parse(
          Buffer.from(access.split('.')[1], 'base64url').toString(),
        )
        if (claims.exp * 1000 > Date.now() + 30000) return token
        const response = await fetch(`${backend()}/refresh`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${String(token.refreshToken)}`,
            'Idempotency-Key': createHmac(
              'sha256',
              String(process.env.NEXTAUTH_SECRET),
            )
              .update(String(token.refreshToken))
              .digest('hex'),
          },
          signal: AbortSignal.timeout(5000),
          cache: 'no-store',
        })
        if (!response.ok) throw new Error('Refresh rejected')
        const renewed = await response.json()
        token.accessToken = renewed.access_token
        token.refreshToken = renewed.refresh_token
      } catch {
        token.accessToken = ''
        token.refreshToken = ''
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string
      const publicUser = { ...((token.user ?? {}) as any) }
      delete publicUser.token
      delete publicUser.refreshToken
      session.user = publicUser
      return session
    },
  },
  events: {
    async signOut(message) {
      if (!('token' in message) || !message.token) return
      for (const value of [
        message.token.accessToken,
        message.token.refreshToken,
      ]) {
        if (!value) continue
        const response = await fetch(`${backend()}/logout`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${String(value)}` },
          signal: AbortSignal.timeout(5000),
        })
        if (!response.ok && response.status !== 401)
          throw new Error('Backend revocation failed')
      }
    },
  },
}
