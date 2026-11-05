// types/next-auth.d.ts
import 'next-auth'

declare module 'next-auth' {
  interface User {
    id: number
    email: string
    name: string
    active: boolean
    token: string
    refreshToken?: string
    is_manager: boolean
    subscriptionactive: boolean
  }

  interface Session {
    accessToken: string
    user: User
  }

  interface JWT {
    accessToken: string
    is_manager: boolean
    id: number
    subscriptionactive: boolean
  }
}
