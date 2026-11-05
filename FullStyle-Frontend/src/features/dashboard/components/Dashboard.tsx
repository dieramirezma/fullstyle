'use client'

import { toast } from 'sonner'
import { StatCard } from './StatCard'
import { SalesChart } from './SalesChart'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { BookingsChart } from './BookingsChart'
import { ChartSkeleton } from './skeletons/ChartSkeleton'
import { StatCardSkeleton } from './skeletons/StatSkeleton'
import type { BookingsData, SalesData } from '../types/types'
import EmptyState from '@/features/shared/components/EmptyState'
import { Building2, Calendar, DollarSign, Users } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  fetchMonthlyBookings,
  fetchMonthlyRevenue,
  fetchSiteIdByManager,
} from '../api/dashboardApi'

export function Dashboard() {
  // Estados para manejar la información del dashboard
  const { data: session } = useSession()
  const [error, setError] = useState<string | null>(null)
  const [siteId, setSiteId] = useState<number | null>(null)
  const [revenueLoading, setRevenueLoading] = useState(true)
  const [salesData, setSalesData] = useState<SalesData[]>([])
  const [bookingsLoading, setBookingsLoading] = useState(true)
  const [bookingsData, setBookingsData] = useState<BookingsData[]>([])
  const [monthlyRevenue, setMonthlyRevenue] = useState<string | null>(null)
  const [monthlyBookings, setMonthlyBookings] = useState<string | null>(null)
  const [revenueChange, setRevenueChange] = useState<{
    text: string
    color: string
  } | null>(null)
  const [bookingsChange, setBookingsChange] = useState<{
    text: string
    color: string
  } | null>(null)

  useEffect(() => {
    const fetchSiteId = async () => {
      if (!session?.user?.is_manager) return // Validar si es un manager

      try {
        const id = await fetchSiteIdByManager(session.user.id)
        if (id) {
          setSiteId(id)
        } else {
          toast.error('No se encontró un negocio asociado a tu cuenta')
        }
      } catch (error) {
        toast.error('No se encontró un negocio asociado a tu cuenta')
        setError('404')
      }
    }

    fetchSiteId()
  }, [session]) // Se ejecuta cuando cambia la sesión

  useEffect(() => {
    if (!siteId) return // Esperamos a que siteId tenga valor
    fetchRevenue(siteId)
    fetchBookings(siteId)
  }, [siteId]) // Se ejecuta cuando `siteId` cambia

  const fetchRevenue = async (siteId: number) => {
    try {
      const statsData = await fetchMonthlyRevenue(siteId)
      const stats = statsData.statistics
      const formattedData = stats.map((stat) => {
        const monthName = new Date(stat.year, stat.month - 1).toLocaleString(
          'es-ES',
          { month: 'short' },
        )
        return {
          name: monthName.charAt(0).toUpperCase() + monthName.slice(1),
          ventas: stat.total_amount,
        }
      })

      setSalesData(formattedData)

      if (stats.length >= 2) {
        const latest = stats[stats.length - 1].total_amount
        const previous = stats[stats.length - 2].total_amount
        const change = ((latest - previous) / previous) * 100

        setRevenueChange({
          text: `${change > 0 ? '+' : '-'} ${change.toFixed(1)}% respecto al mes anterior`,
          color: change > 0 ? 'text-green-500' : 'text-red-500',
        })

        setMonthlyRevenue(`$${latest.toLocaleString()}`)
      } else if (stats.length === 1) {
        setMonthlyRevenue(`$${stats[0].total_amount.toLocaleString()}`)
        setRevenueChange({
          text: 'No hay datos del mes anterior',
          color: 'text-gray-500',
        })
      }
      setRevenueLoading(false)
    } catch (error) {
      console.error('Error fetching revenue:', error)
    }
  }

  const fetchBookings = async (siteId: number) => {
    try {
      const statsData = await fetchMonthlyBookings(siteId)
      const stats = statsData.statistics
      const formattedData = stats.map((stat) => {
        const monthName = new Date(stat.year, stat.month - 1).toLocaleString(
          'es-ES',
          { month: 'short' },
        )
        return {
          name: monthName.charAt(0).toUpperCase() + monthName.slice(1),
          Reservas: stat.total,
        }
      })

      setBookingsData(formattedData)

      if (stats.length >= 2) {
        const latest = stats[stats.length - 1].total
        const previous = stats[stats.length - 2].total
        const change = ((latest - previous) / previous) * 100

        setBookingsChange({
          text: `${change.toFixed(1)}% ${change > 0 ? 'más' : 'menos'} respecto al mes anterior`,
          color: change > 0 ? 'text-green-500' : 'text-red-500',
        })

        setMonthlyBookings(`${latest}`)
      } else if (stats.length === 1) {
        setMonthlyBookings(`${stats[0].total}`)
        setBookingsChange({
          text: 'No hay datos del mes anterior',
          color: 'text-gray-500',
        })
      }
      setBookingsLoading(false)
    } catch (error) {
      console.error('Error fetching bookings:', error)
    }
  }

  if (error === '404') {
    return (
      <EmptyState
        icon={<Building2 className="h-12 w-12 text-primary" />}
        title="No tienes ningún negocio creado"
        description="Crea tu primer negocio para comenzar a recibir reservas y gestionar tus servicios"
        actionHref="/owner/business"
        actionLabel="Crear negocio"
      />
    )
  }
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight title">
        Resumen de tu negocio
      </h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {revenueLoading ? (
          <StatCardSkeleton />
        ) : (
          <StatCard
            title="Ingresos del mes"
            value={monthlyRevenue ?? '$0'}
            description={revenueChange}
            icon={DollarSign}
          />
        )}
        {bookingsLoading ? (
          <StatCardSkeleton />
        ) : (
          <StatCard
            title="Reservas del mes"
            value={monthlyBookings ?? '0'}
            description={bookingsChange}
            icon={Calendar}
          />
        )}
        {bookingsLoading ? (
          <StatCardSkeleton />
        ) : (
          <StatCard
            title="Nuevos clientes"
            value="0"
            description={{ text: 'Este mes', color: 'text-green-500' }}
            icon={Users}
          />
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {revenueLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Ventas</CardTitle>
            </CardHeader>
            <CardContent>
              <SalesChart data={salesData} />
            </CardContent>
          </Card>
        )}
        {bookingsLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Reservas</CardTitle>
            </CardHeader>
            <CardContent>
              <BookingsChart data={bookingsData} />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
