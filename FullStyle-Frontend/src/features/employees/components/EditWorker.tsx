'use client'

import { useForm } from 'react-hook-form'
import apiClient from '@/utils/apiClient'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { zodResolver } from '@hookform/resolvers/zod'
import LoadingSpinner from '@/features/shared/components/LoadingSpinner'
import { type Site, type Worker } from '@/features/employees/types/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import {
  userSchema,
  type UserSchemaValues,
} from '@/features/employees/types/schemas'
import {
  fetchSiteByManager,
  fetchWorkersBySite,
} from '@/features/employees/api/workerApi'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/features/shared/components/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function EditWorker() {
  const { data: session, status } = useSession()
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [workers, setWorkers] = useState<Worker[]>([])
  const [site, setSite] = useState<Site | null>(null)
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null)

  const form = useForm<UserSchemaValues>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  })

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const managerId = session?.user?.id
        if (!managerId) {
          throw new Error('Manager ID is not available')
        }
        const siteData = await fetchSiteByManager(managerId)

        if (siteData) {
          setSite({
            id: siteData.id,
            name: siteData.name,
            address: siteData.address,
            phone: siteData.phone,
          })
          const siteId = siteData?.id as number
          const workersData = await fetchWorkersBySite(siteId)
          setWorkers(workersData)
        } else {
          setError('No se encontró información del negocio.')
        }
      } catch (error) {
        console.error('Error al obtener datos:', error)
        setError('Error al obtener la información.')
      } finally {
        setLoading(false)
      }
    }

    if (session && session.user.active) {
      fetchData()
    }
  }, [session])

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }
  if (status !== 'authenticated')
    return <a href="/api/auth/signin">Iniciar sesión</a>
  if (!session.user.active) {
    return <p>Usuario no activo</p>
  }

  const handleEdit = async (values: UserSchemaValues) => {
    if (!selectedWorkerId) {
      setError('Por favor, selecciona un trabajador para editar.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccessMessage(null)

    const payload = {
      name: values.name,
      site_id: site?.id,
      description: values.description,
    }
    console.log(payload)
    try {
      await apiClient.put(`worker?id=${selectedWorkerId}`, payload)
      setWorkers((prevWorkers) =>
        prevWorkers.map((worker) =>
          worker.id === Number(selectedWorkerId)
            ? { ...worker, name: values.name }
            : worker,
        ),
      )
      setSuccessMessage('Trabajador actualizado correctamente.')
      form.setValue('name', '')
      form.setValue('description', '')
      setSelectedWorkerId(null)
    } catch (error: any) {
      const errorMessage: string =
        error &&
        typeof error === 'object' &&
        'response' in error &&
        error.response?.data?.message
          ? error.response.data.message
          : 'Error al actualizar el trabajador.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="flex flex-col items-center space-y-6 p-6 max-w-2xl mx-auto">
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">
            Información del Negocio
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name" className="font-semibold">
                Nombre:
              </Label>
              <div id="name" className="p-2 bg-gray-100 rounded-md">
                {site?.name}
              </div>
            </div>
            <div>
              <Label htmlFor="phone" className="font-semibold">
                Teléfono:
              </Label>
              <div id="phone" className="p-2 bg-gray-100 rounded-md">
                {site?.phone}
              </div>
            </div>
          </div>
          <div>
            <Label htmlFor="address" className="font-semibold">
              Dirección:
            </Label>
            <div id="address" className="p-2 bg-gray-100 rounded-md">
              {site?.address}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-xl font-bold">
            Actualizar Trabajador
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="worker-select" className="font-semibold">
              Selecciona un trabajador:
            </Label>
            <Select onValueChange={setSelectedWorkerId}>
              <SelectTrigger id="worker-select">
                <SelectValue placeholder="Selecciona un trabajador" />
              </SelectTrigger>
              <SelectContent>
                {workers.map((worker) => (
                  <SelectItem key={worker.id} value={worker.id.toString()}>
                    {worker.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Form {...form}>
            <form
              className="flex flex-col gap-y-4"
              onSubmit={form.handleSubmit(handleEdit)}
            >
              <FormField
                name="name"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">Nuevo nombre</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="description"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Nueva Descripcion
                    </FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex flex-col items-center">
                {successMessage && (
                  <p className="text-green-500 mb-2">{successMessage}</p>
                )}
                {error && <p className="text-red-500 mb-2">{error}</p>}
                <Button
                  type="submit" // ✅ Ahora el formulario manejará el submit correctamente
                  className="bg-red-500 hover:bg-red-600 text-white"
                  disabled={loading || !selectedWorkerId}
                >
                  {loading
                    ? 'Actualizando trabajador...'
                    : 'Actualizar trabajador'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
