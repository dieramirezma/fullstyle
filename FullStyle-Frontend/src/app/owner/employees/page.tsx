'use client'

import axios from 'axios'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { Button } from '@/components/ui/button'
import { Building2, Plus, Scissors } from 'lucide-react'
import { type Service } from '@/features/employees/types/types'
import EmptyState from '@/features/shared/components/EmptyState'
import DeleteWorker from '@/features/employees/components/DeleteWorker'
import LoadingSpinner from '@/features/shared/components/LoadingSpinner'
import { AddWorkerDialog } from '../../../features/employees/components/AddWorkerDialog'
import {
  fetchServicesBySite,
  fetchSiteByManager,
} from '@/features/employees/api/workerApi'

function Page() {
  const { data: session } = useSession()
  const [workerRevision, setWorkerRevision] = useState(0)
  const [services, setServices] = useState<Service[]>([])
  const [siteId, setSiteId] = useState<number | null>(null)
  const [error, setError] = useState<{ code: number; type: string } | null>(
    null,
  )
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [showButton, setShowButton] = useState(true)

  useEffect(() => {
    fetchSiteAndServices()
  }, [session?.user.id])

  const fetchSiteAndServices = async () => {
    if (session?.user?.id) {
      try {
        const site = await fetchSiteByManager(session.user.id)
        const siteId = site?.id as number
        setSiteId(siteId)

        try {
          const servicesData = await fetchServicesBySite(siteId)
          setServices(servicesData)
        } catch (error) {
          if (axios.isAxiosError(error) && error.response?.status === 404) {
            setError({ code: 404, type: 'services' })
          }
        }
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          setError({ code: 404, type: 'site' })
        }
      } finally {
        setLoading(false)
      }
    }
  }

  const handleWorkerAdded = () => {
    setWorkerRevision((revision) => revision + 1)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error?.code === 404 && error.type === 'services') {
    return (
      <EmptyState
        icon={<Scissors className="h-12 w-12 text-primary" />}
        title="No tienes ningún servicio creado"
        description="Crea tu primer servicio para comenzar a recibir reservas y gestionar tus servicios"
        actionHref="/owner/services"
        actionLabel="Crear servicio"
      />
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex flex-col justify-between w-full sm:flex-row sm:items-center">
          <h1 className="title">Gestiona tus empleados</h1>
          {showButton && (
            <Button
              onClick={() => {
                setOpen(true)
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              Agregar Trabajador
            </Button>
          )}
        </div>
        {siteId && (
          <AddWorkerDialog
            siteId={siteId}
            services={services}
            onWorkerAdded={handleWorkerAdded}
            open={open}
            setOpen={setOpen}
          />
        )}
      </div>
      <DeleteWorker
        key={workerRevision}
        showButton={showButton}
        setShowButton={setShowButton}
      />
    </div>
  )
}

export default Page
