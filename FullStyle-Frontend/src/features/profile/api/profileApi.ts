import apiClient from '@/utils/apiClient'

export async function updateUserPassword(
  userId: number,
  password: string,
  name: string,
  email: string,
) {
  return await apiClient.put(`user/${userId}`, { password, name, email })
}
