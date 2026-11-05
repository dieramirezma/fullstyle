import { type LucideIcon } from 'lucide-react'

export interface SiteStatistics {
  site_id: number
  period: string
  count_periods: number
  statistics: Array<{
    year: number
    month: number
    total_amount: number
  }>
}

export interface BookingStatistics {
  site_id: number
  period: string
  count_periods: number
  statistics: Array<{
    year: number
    month: number
    total: number
  }>
}

export interface StatCardProps {
  title: string
  value: string
  description?: { text: string; color: string } | null
  icon: LucideIcon
}

export interface BookingsData {
  name: string
  Reservas: number
}
export interface SalesData {
  name: string
  ventas: number
}
