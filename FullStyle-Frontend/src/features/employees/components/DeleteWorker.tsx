'use client'

import axios from 'axios'
import Image from 'next/image'
import { toast } from 'sonner'
import EmptyState from '../../shared/components/EmptyState'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Button } from '@/components/ui/button'
import WorkerScheduleForm from './WorkerScheduleForm'
import { Card, CardContent } from '@/components/ui/card'
import { UserCircle2, Trash2, Users } from 'lucide-react'
import LoadingSpinner from '../../shared/components/LoadingSpinner'
import {
  type Worker,
  type Site,
  type DeleteWorkerProps,
} from '@/features/employees/types/types'
import {
  deleteWorkerById,
  fetchSiteByManager,
  fetchWorkersBySite,
} from '@/features/employees/api/workerApi'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

export default function DeleteWorker({
  showButton,
  setShowButton,
}: DeleteWorkerProps) {
  const { data: session, status } = useSession()
  const [loading, setLoading] = useState(false)
  const [workers, setWorkers] = useState<Worker[]>([])
  const [, setSite] = useState<Site | null>(null)
  const [workerToDelete, setWorkerToDelete] = useState<Worker | null>(null)
  const [error, setError] = useState<{ code: number; type: string } | null>(
    null,
  )

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const managerId = session?.user?.id
        if (!managerId) {
          throw new Error('Manager ID is not available')
        }
        const siteData = await fetchSiteByManager(managerId)
        setSite({
          id: siteData.id,
          name: siteData.name,
          address: siteData.address,
          phone: siteData.phone,
        })

        try {
          const siteId = siteData?.id as number
          const workersData = await fetchWorkersBySite(siteId)
          setWorkers(workersData)
        } catch (error) {
          if (axios.isAxiosError(error) && error.response?.status === 404) {
            setError({ code: 404, type: 'workers' })
            setShowButton && setShowButton(false)
          } else {
            setError({ code: 500, type: 'workers' })
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

    if (session && session.user.active) {
      fetchData()
    }
  }, [session])

  const handleDelete = async (worker: Worker) => {
    setLoading(true)
    try {
      await deleteWorkerById(worker.id)
      setWorkers((prevWorkers) => prevWorkers.filter((w) => w.id !== worker.id))
      toast.success('Éxito', {
        description: 'El empleado ha sido eliminado correctamente',
      })
    } catch (error: any) {
      toast.error('Error', {
        description:
          error.response?.data?.message || 'Error al eliminar el trabajador.',
      })
    } finally {
      setLoading(false)
      setWorkerToDelete(null)
    }
  }

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  if (error?.code === 404 && error.type === 'workers') {
    return (
      <EmptyState
        icon={<Users className="h-12 w-12 text-primary" />}
        title="No tienes ningún empleado creado"
        description="Crea tu primer empleado para comenzar a gestionar tu negocio"
      >
        <WorkerScheduleForm className="w-full" urlCallback="/owner" />
      </EmptyState>
    )
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {workers.map((worker) => (
        <Card key={worker.id} className="overflow-hidden">
          <CardContent className="p-6">
            <div className="flex flex-col items-center text-center space-y-4">
              {worker.profilepicture ? (
                <div className="relative w-24 h-24 rounded-full overflow-hidden">
                  <Image
                    src={worker.profilepicture || '/placeholder.svg'}
                    alt={worker.name}
                    fill
                    className="object-cover"
                  />
                </div>
              ) : (
                <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center">
                  <UserCircle2 className="w-16 h-16 text-muted-foreground" />
                </div>
              )}
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">{worker.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {worker.description}
                </p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                className="w-full"
                onClick={() => {
                  setWorkerToDelete(worker)
                }}
                disabled={loading}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Eliminar
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}

      <AlertDialog
        open={!!workerToDelete}
        onOpenChange={() => {
          setWorkerToDelete(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Estás seguro?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción eliminará permanentemente a {workerToDelete?.name} y
              no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-500 hover:bg-red-600"
              onClick={async () =>
                await (workerToDelete && handleDelete(workerToDelete))
              }
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {error && (
        <div className="col-span-full text-center text-red-500">
          {error.type}
        </div>
      )}

      {workers.length === 0 && !loading && !error && (
        <div className="col-span-full text-center text-muted-foreground">
          No hay trabajadores registrados.
        </div>
      )}
    </div>
  )
}
