import apiClient from '@/utils/apiClient'
import type { Service } from '../types/types'
import { type Worker } from '@/features/employees/types/types'

// Upload worker image
export async function uploadWorkerImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('image', file)
  const response = await apiClient.post('/api/upload-media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  if (!response.data.success) throw new Error(String(response.data.message))
  return response.data.url
}

// Create worker and return workerId
export async function createWorker(data: {
  name: string
  site_id: number
  description: string
  services: number[]
  profilepicture: string
}): Promise<number> {
  const response = await apiClient.post('worker', data)
  return response.data.id
}

// Delete worker by ID
export async function deleteWorkerById(workerId: number) {
  return await apiClient.delete(`worker?id=${workerId}`)
}

// Update worker by ID
export async function updateWorkerById(
  workerId: number,
  payload: { name: string; site_id: number; description: string },
) {
  return await apiClient.put(`worker?id=${workerId}`, payload)
}

// Fetch workers by site ID
export async function fetchWorkersBySite(siteId: number): Promise<Worker[]> {
  const response = await apiClient.get(`worker?site_id=${siteId}`)
  return response.data
}

export async function fetchWorkersBySiteAndService(
  siteId: string,
  serviceId: string,
): Promise<Worker[]> {
  const response = await apiClient.get(
    `worker?site_id=${siteId}&service_id=${serviceId}`,
  )
  return response.data
}

// Assign services to worker
export async function assignWorkerServices(
  workerId: number,
  services: number[],
) {
  return await Promise.all(
    services.map(
      async (serviceId) =>
        await apiClient.post('worker_has_service', {
          worker_id: workerId,
          service_id: serviceId,
        }),
    ),
  )
}

// Assign schedule to worker
export async function assignWorkerSchedule(
  workerId: number,
  schedule: Record<string, { startTime: string; endTime: string }>,
) {
  return await Promise.all(
    Object.entries(schedule).map(
      async ([day, time]) =>
        await apiClient.post('availability', {
          worker_id: workerId,
          weekday: day,
          starttime: time.startTime,
          endtime: time.endTime,
        }),
    ),
  )
}

// Fetch site by manager ID
export async function fetchSiteByManager(managerId: number) {
  const response = await apiClient.get(`site?manager_id=${managerId}`)
  // Assuming the API returns an array, return the first site
  return response.data[0]
}

// Fetch services by site ID
export async function fetchServicesBySite(siteId: number): Promise<Service[]> {
  const response = await apiClient.get(`detail?site_id=${siteId}`)
  // Map to your Service type if needed
  return response.data.map((detail: any) => ({
    service_id: detail.service_id,
    service_name: detail.service_name,
  }))
}
