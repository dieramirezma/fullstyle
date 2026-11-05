'use client'

import axios from 'axios'
import { useSession } from 'next-auth/react'
import { Button } from '@/components/ui/button'
import { fetchServices } from '@/utils/servicesUtils'
import { useEffect, useState, useCallback } from 'react'
import { Building2, Plus, Scissors } from 'lucide-react'
import EmptyState from '@/features/shared/components/EmptyState'
import type { Detail, Service } from '@/features/services/types/types'
import LoadingSpinner from '@/features/shared/components/LoadingSpinner'
import { ServiceList } from '../../../features/services/components/ServiceList'
import RegisterServiceForm from '@/features/services/components/RegisterServicesForm'
import {
  fetchSiteAndDetails,
  updateService,
} from '@/features/services/api/servicesApi'
import { AddServiceDialog } from '../../../features/services/components/AddServiceDialog'

function Page() {
  const { data: session, status } = useSession()
  const [site, setSite] = useState({ id: 0, name: '', address: '', phone: '' })
  const [details, setDetails] = useState<Detail[]>([])
  const [availableServices, setAvailableServices] = useState<
    Array<{ id: number; category_id: number; name: string }>
  >([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ code: number; type: string } | null>(
    null,
  )
  const [open, setOpen] = useState(false)
  const managerId = session?.user.id

  const fetchSiteAndDetailsCallback = useCallback(async () => {
    setLoading(true)
    try {
      if (!managerId) return
      const { site, details, availableServices } =
        await fetchSiteAndDetails(managerId)
      if (site) setSite(site)
      if (details) setDetails(details)
      if (availableServices) setAvailableServices(availableServices)
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        setError({ code: 404, type: 'site' })
      }
    } finally {
      setLoading(false)
    }
  }, [managerId])

  useEffect(() => {
    const getServices = async () => {
      const servicesData = await fetchServices()
      setAvailableServices(servicesData.available)
    }
    getServices()
  }, [])

  useEffect(() => {
    if (status === 'authenticated' && managerId) {
      fetchSiteAndDetailsCallback()
    }
  }, [managerId, status, fetchSiteAndDetailsCallback])

  const handleServiceClick = (serviceId: number) => {
    console.log(`Service clicked: ${serviceId}`)
  }

  const handleServiceUpdate = async (updatedService: Service) => {
    try {
      await updateService(updatedService)
      setDetails((prevDetails) =>
        prevDetails.map((detail) =>
          detail.service_id === updatedService.service_id
            ? { ...detail, ...updatedService }
            : detail,
        ),
      )
    } catch (error) {
      console.error('Error updating service:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error?.code === 404 && error.type === 'site') {
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

  if (error?.code === 404 && error.type === 'services') {
    return (
      <EmptyState
        icon={<Scissors className="h-12 w-12 text-primary" />}
        title="No tienes ningún servicio creado"
        description="Crea servicios para comenzar a recibir reservas y gestionar tus empleados"
      >
        <RegisterServiceForm
          className="w-full"
          urlCallback="/owner/employees"
        />
      </EmptyState>
    )
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex flex-col justify-between w-full sm:flex-row sm:items-center">
        <h1 className="title">Gestiona tus servicios</h1>
        <Button
          onClick={() => {
            setOpen(true)
          }}
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar servicio
        </Button>
      </div>
      <AddServiceDialog
        siteId={site.id}
        services={availableServices}
        onServiceAdded={fetchSiteAndDetailsCallback}
        open={open}
        setOpen={setOpen}
      />
      <ServiceList
        services={details.map((detail) => ({
          service_id: detail.service_id,
          site_id: detail.site_id,
          service_name: detail.service_name,
          price: detail.price,
          duration: detail.duration,
          photos: detail?.photos,
          description: detail?.description ?? undefined,
        }))}
        onServiceClick={handleServiceClick}
        onServiceUpdate={handleServiceUpdate}
      />
    </div>
  )
}

export default Page
