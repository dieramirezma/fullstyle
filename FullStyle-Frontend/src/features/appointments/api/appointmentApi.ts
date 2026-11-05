import apiClient from '@/utils/apiClient'
import type {
  Site,
  Worker,
  WeeklySchedule,
  Detail,
  AppointmentData,
} from '../types/types'
import { format } from 'date-fns'

// Fetch sites by service
export async function fetchSitesByService(serviceId: string) {
  const response = await apiClient.get<Site[]>(`site?service_id=${serviceId}`)
  return response.data
}

// Fetch workers by site and service
export async function fetchWorkersBySiteAndService(
  siteId: number,
  serviceId: string,
) {
  const response = await apiClient.get<Worker[]>(
    `worker?site_id=${siteId}&service_id=${serviceId}`,
  )
  return response.data
}

// Fetch site detail
export async function fetchSiteDetail(siteId: number) {
  const response = await apiClient.get<Site[]>(`site?id=${siteId}`)
  return response.data
}

// Fetch worker detail
export async function fetchWorkerDetail(workerId: number) {
  const response = await apiClient.get<Worker[]>(`worker?id=${workerId}`)
  return response.data
}

// Fetch weekly schedule
export async function fetchWeeklySchedule(workerId: number, weekStart: Date) {
  const response = await apiClient.get<WeeklySchedule>(
    'worker/weekly_schedule',
    {
      params: {
        worker_id: workerId,
        date: format(weekStart, 'yyyy-MM-dd'),
      },
    },
  )
  return response.data
}

// Fetch service detail
export async function fetchServiceDetail(serviceId: number, siteId: number) {
  const response = await apiClient.get<Detail[]>(
    `detail?service_id=${serviceId}&site_id=${siteId}`,
  )
  return response.data
}

// Create appointment
export async function createAppointment(appointmentData: AppointmentData) {
  return await apiClient.post('appointment', appointmentData)
}

// Search sites
export async function searchSites(params: { name?: string; address?: string }) {
  const response = await apiClient.get<Site[]>('site', { params })
  return response.data
}

// Fetch all services
export async function fetchAllServices() {
  const response = await apiClient.get('service')
  return response.data
}

// Fetch all categories
export async function fetchAllCategories() {
  const response = await apiClient.get('category')
  return response.data
}
