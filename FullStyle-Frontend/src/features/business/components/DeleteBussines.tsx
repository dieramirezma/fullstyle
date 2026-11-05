'use client'

import router from 'next/router'
import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { Label } from '@radix-ui/react-label'
import { Button } from '../../../components/ui/button'
import LoadingSpinner from '../../shared/components/LoadingSpinner'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../../components/ui/card'
import {
  deleteBusiness,
  fetchBusinessByManager,
} from '@/features/business/api/businessApi'

export default function DeleteSite() {
  const [loading, setLoading] = useState(false)
  const { data: session, status } = useSession()
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [site, setSite] = useState<{
    id: number
    name: string
    address: string
    phone: string
  } | null>(null)

  useEffect(() => {
    const fetchSite = async () => {
      setError('')
      try {
        const managerId = session?.user.id
        if (!managerId) {
          setError('No se pudo obtener el ID del gerente.')
          return
        }
        const siteData = await fetchBusinessByManager(managerId)
        if (siteData) {
          setSite(siteData)
        } else {
          setError('No se encontró información del negocio.')
        }
      } catch (error) {
        console.error('Error al obtener el sitio:', error)
        setError('Error al obtener la información del negocio.')
      } finally {
        setLoading(false)
      }
    }
    fetchSite()
  }, [session, status])

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
    setLoading(false)
  }
  const handleDelete = async () => {
    if (!session.user.id) {
      setError('No se pudo obtener el ID del usuario.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccessMessage(null)

    try {
      if (site?.id) {
        await deleteBusiness(site.id)
      } else {
        setError('No se pudo obtener el ID del sitio.')
        return
      }
      setSuccessMessage('Sitio eliminado correctamente.')
    } catch (error: any) {
      const errorMessage =
        error &&
        typeof error === 'object' &&
        'response' in error &&
        error.response?.data?.message
          ? error.response.data.message
          : 'Error al eliminar el sitio.'
      setError(errorMessage as string)
    } finally {
      router.push('/customer')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center space-y-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Información del Negocio</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nombre:</Label>
            <div id="name" className="p-2 bg-gray-100 rounded-md">
              {site?.name ?? 'No disponible'}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Dirección:</Label>
            <div id="address" className="p-2 bg-gray-100 rounded-md">
              {site?.address ?? 'No disponible'}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Teléfono:</Label>
            <div id="phone" className="p-2 bg-gray-100 rounded-md">
              {site?.phone ?? 'No disponible'}
            </div>
          </div>
        </CardContent>
      </Card>
      {successMessage && <p className="text-green-500">{successMessage}</p>}
      {error && <p className="text-red-500">{error}</p>}
      <Button
        type="submit"
        onClick={handleDelete}
        className="bg-red-500 text-white px-4 py-2 rounded"
        disabled={loading}
      >
        {loading ? 'Eliminando sitio' : 'Eliminar sitio'}
      </Button>
    </div>
  )
}
