import apiClient from '@/utils/apiClient'
import { type Site } from '@/features/business/types/types'

export async function uploadBusinessImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('image', file)
  const response = await apiClient.post('/api/upload-media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  if (!response.data.success) {
    const errorMessage =
      typeof response.data.message === 'string'
        ? response.data.message
        : 'Unknown error'
    throw new Error(errorMessage as string)
  }
  return response.data.url
}

export async function createBusiness(payload: {
  name: string
  address: string
  phone: string
  manager_id: number
  photos: Record<string, string>
}) {
  return await apiClient.post('site', payload)
}

export async function fetchBusinessByManager(
  managerId: number,
): Promise<Site | null> {
  const response = await apiClient.get(`site?manager_id=${managerId}`)
  if (Array.isArray(response.data) && response.data.length > 0) {
    return response.data[0]
  }
  return null
}

export async function updateBusiness(siteId: number, payload: Partial<Site>) {
  return await apiClient.put(`site?id=${siteId}`, payload)
}

export async function deleteBusiness(siteId: number) {
  return await apiClient.delete(`site?id=${siteId}`)
}

export async function assignCategoriesToSite(
  siteId: number,
  categoryIds: number[],
) {
  const promises = categoryIds.map(async (categoryId) => {
    const payload = {
      site_id: siteId,
      category_id: categoryId,
    }
    return await apiClient.post('site_has_category', payload)
  })
  return await Promise.all(promises)
}
