import apiClient from '@/utils/apiClient'

export async function registerOwner(payload: {
  name: string
  email: string
  password: string
  bankaccount: string
  accounttype: string
  bankentity: string
}) {
  return await apiClient.post('manager_register', payload)
}

export async function registerCustomer(payload: {
  name: string
  email: string
  password: string
}) {
  const query = `
    mutation RegisterUser($name: String!, $email: String!, $password: String!) {
      registerUser(name: $name, email: $email, password: $password) {
        message
        user {
          active
          email
          id
          name
        }
      }
    }
  `

  const response = await fetch('/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      variables: {
        name: payload.name,
        email: payload.email,
        password: payload.password,
      },
    }),
  })

  const result = await response.json()

  if (!response.ok || result.errors) {
    throw new Error(
      String(result.errors?.[0]?.message ?? 'Registration failed'),
    )
  }

  return result.data.registerUser
}

export async function registerWithGoogle(payload: {
  name: string
  email: string
}) {
  return await apiClient.post('register_google', payload, {
    withCredentials: true,
  })
}

export async function requestPasswordReset(email: string) {
  return await apiClient.post('user/reset-password-request', { email })
}

export async function resetPassword(payload: {
  password: string
  token: string
}) {
  return await apiClient.post('user/reset-password', payload)
}

export async function enable2FA(email: string, password: string) {
  return await apiClient.post('enable-2fa', { email, password })
}

export async function verify2FA(email: string, otp: string, password: string) {
  return await apiClient.post('verify-2fa', { email, otp, password })
}
