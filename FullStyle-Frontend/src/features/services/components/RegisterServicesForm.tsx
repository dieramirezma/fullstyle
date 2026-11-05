'use client'

import Link from 'next/link'
import Image from 'next/image'
import { toast } from 'sonner'
import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ImageIcon, Loader2, X } from 'lucide-react'
import { Input } from '../../../components/ui/input'
import { fetchServices } from '@/utils/servicesUtils'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { DURATIONOPTIONS } from '@/features/services/types/constants'
import { createService, uploadServiceImage } from '../api/servicesApi'
import {
  userSchema,
  type UserSchemaValues,
} from '@/features/services/types/schemas'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '../../shared/components/form'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../../../components/ui/card'

export default function RegisterServiceForm({
  className,
  urlCallback,
}: {
  className?: string
  urlCallback?: string
}) {
  const form = useForm<UserSchemaValues>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      description: '',
      price: '',
      duration: '',
      photos: {},
    },
  })

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [services, setServices] = useState<
    Array<{ id: number; category_id: number; name: string }>
  >([])
  const [uploadingImage, setUploadingImage] = useState(false)
  const [photos, setPhotos] = useState<Record<string, string>>({})
  const [photoCount, setPhotoCount] = useState(0)

  const router = useRouter()

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    // Verificar que sea una imagen
    if (!file.type.startsWith('image/')) {
      setError('El archivo debe ser una imagen')
      return
    }

    setUploadingImage(true)
    setError('')

    try {
      const url = await uploadServiceImage(file)
      const photoKey = `photo${photoCount + 1}`
      const newPhotos = { ...photos, [photoKey]: url }
      setPhotos(newPhotos)
      setPhotoCount((prev) => prev + 1)
      form.setValue('photos', newPhotos)
    } catch (err: any) {
      setError(
        'Error al subir la imagen: ' + (err.message || 'Error desconocido'),
      )
    } finally {
      setUploadingImage(false)
      // Limpiar el input para permitir subir la misma imagen nuevamente
      e.target.value = ''
    }
  }

  function removePhoto(key: string) {
    const newPhotos = Object.fromEntries(
      Object.entries(photos).filter(([k]) => k !== key),
    )
    setPhotos(newPhotos)
    form.setValue('photos', newPhotos)
  }

  useEffect(() => {
    const getServices = async () => {
      const servicesData = await fetchServices()
      setServices(servicesData.available)
    }
    getServices()
  }, [])

  async function onSubmit(values: UserSchemaValues) {
    setError('')
    setSuccessMessage('')
    setLoading(true)
    const siteId = localStorage.getItem('siteId') as unknown as number
    const payload = {
      site_id: siteId,
      service_id: values.service,
      description: values.description,
      price: values.price,
      duration: values.duration,
      photos: values.photos,
    }

    try {
      await createService(payload)
      setServices((prevServices) =>
        prevServices.filter((service) => service.id !== Number(values.service)),
      )
      form.setValue('service', '')
      toast.success('Servicio agregado de forma exitosa')
      if (urlCallback) {
        router.push(urlCallback)
      }
    } catch (error: any) {
      setSuccessMessage('')
      if (error.response.data.message !== undefined) {
        setError(String(error.response.data.message))
      } else {
        setError('Ocurrió un error inesperado. Inténtalo de nuevo más tarde.')
      }
    } finally {
      setLoading(false)
    }
  }
  return (
    <Card className={className ?? 'w-full md:w-1/2'}>
      <CardHeader>
        <CardTitle className="subtitle text-center">
          Registro de Nuevo Servicio
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <CardDescription className="text-xl text-black ">
              Datos del servicio
            </CardDescription>
            <FormField
              control={form.control}
              name="service"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Servicio<span className="text-red-500"> *</span>
                  </FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona el servicio" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {services.map((service) => (
                        <SelectItem key={service.id} value={String(service.id)}>
                          {service.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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
                    Descripcion del servicio
                    <span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="price"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Precio<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input type="number" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="duration"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Duración<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona la duración" />
                      </SelectTrigger>
                      <SelectContent>
                        {DURATIONOPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="photos"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Foto del servicio
                  </FormLabel>
                  <div className="space-y-4">
                    <div className="flex flex-wrap gap-4">
                      {Object.entries(photos).map(([key, url]) => (
                        <div
                          key={key}
                          className="relative w-24 h-24 rounded-md overflow-hidden border"
                        >
                          <Image
                            src={url || '/placeholder.svg'}
                            alt={`Foto ${key}`}
                            fill
                            className="object-cover"
                          />
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            className="absolute top-1 right-1 h-6 w-6"
                            onClick={() => {
                              removePhoto(key)
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}

                      <div className="w-24 h-24 flex items-center justify-center border border-dashed rounded-md">
                        <label
                          htmlFor="image-upload"
                          className="cursor-pointer flex flex-col items-center justify-center w-full h-full"
                        >
                          {uploadingImage ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                          ) : (
                            <>
                              <ImageIcon className="h-6 w-6 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground mt-1">
                                Subir foto
                              </span>
                            </>
                          )}
                          <input
                            id="image-upload"
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={handleImageUpload}
                            disabled={uploadingImage}
                          />
                        </label>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Sube una foto de tu servicio para que los clientes puedan
                      verlo
                    </p>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {successMessage.length > 0 && !loading && (
              <p className="text-green-500 text-sm self-center">
                {successMessage}
              </p>
            )}
            {error.length > 0 && (
              <p className="text-red-500 text-sm self-center">{error}</p>
            )}
            <CardFooter className="flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-y-0 sm:space-x-4">
              <Button
                type="submit"
                className="w-full sm:w-auto"
                disabled={loading}
              >
                {loading ? 'Agregando...' : 'AGREGAR UN NUEVO SERVICIO'}
              </Button>
              {!urlCallback && (
                <Button variant="outline" className="w-full sm:w-auto">
                  <Link href={'/register/worker'}>
                    Continuar con el registro{' '}
                  </Link>
                </Button>
              )}
            </CardFooter>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
