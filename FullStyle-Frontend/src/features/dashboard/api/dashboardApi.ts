import apiClient from '@/utils/apiClient'
import type { SiteStatistics, BookingStatistics } from '../types/types'

// Fetch site by manager
export async function fetchSiteIdByManager(
  managerId: number,
): Promise<number | null> {
  const response = await apiClient.get<Array<{ id: number }>>('site', {
    params: { manager_id: managerId },
  })
  return response.data.length > 0 ? response.data[0].id : null
}

// Fetch monthly revenue statistics
export async function fetchMonthlyRevenue(siteId: number) {
  const response = await apiClient.get<SiteStatistics>(
    'payment/site_statistics',
    {
      params: { site_id: siteId, period: 'monthly' },
    },
  )
  return response.data
}

// Fetch monthly bookings statistics
export async function fetchMonthlyBookings(siteId: number) {
  const response = await apiClient.get<BookingStatistics>(
    'appointment/site_statistics',
    {
      params: { site_id: siteId, period: 'monthly' },
    },
  )
  return response.data
}
