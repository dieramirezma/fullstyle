import apiClient from '@/utils/apiClient'
import type { Site, Detail, Service } from '@/features/services/types/types'

// Fetch all services by categories (for available services)
export async function fetchAllServicesByCategories(categories: number[]) {
  const serviceRequests = categories.map(
    async (categoryId) =>
      await apiClient.get(`service?category_id=${categoryId}`),
  )
  const servicesByCategory = await Promise.all(serviceRequests)
  const allServices = servicesByCategory.flatMap((response) => response.data)
  const servicesData = {
    available: allServices,
    selected: [],
  }
  localStorage.setItem('servicesData', JSON.stringify(servicesData))
  return servicesData
}

// Fetch site and its details/services
export async function fetchSiteAndDetails(managerId: number) {
  const response = await apiClient.get(`site?manager_id=${managerId}`)
  const data: Site[] = response.data
  if (!data[0]) return { site: null, details: [], availableServices: [] }
  const site = data[0]
  const [detailsResponse, servicesResponse] = await Promise.all([
    apiClient.get(`detail?site_id=${site.id}&limit=10`),
    apiClient.get('service'),
  ])
  return {
    site,
    details: detailsResponse.data as Detail[],
    availableServices: servicesResponse.data as Array<{
      id: number
      category_id: number
      name: string
    }>,
  }
}

// Update a service
export async function updateService(updatedService: Service) {
  return await apiClient.put(
    `detail?site_id=${updatedService.site_id}&service_id=${updatedService.service_id}`,
    updatedService,
  )
}

// Create a new service
export async function createService(payload: {
  site_id: number
  service_id: string
  description: string
  price: string
  duration: string
  photos: Record<string, string> | undefined
}) {
  return await apiClient.post('detail', payload)
}

// Upload service image
export async function uploadServiceImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('image', file)
  const response = await apiClient.post('/api/upload-media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  if (!response.data.success) {
    const errorMessage =
      typeof response.data.message === 'string'
        ? response.data.message
        : 'An unknown error occurred'
    throw new Error(errorMessage as string)
  }
  return response.data.url
}
