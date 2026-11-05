'use client'

import Image from 'next/image'
import { toast } from 'sonner'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ImageIcon, Loader2, X } from 'lucide-react'
import { zodResolver } from '@hookform/resolvers/zod'
import { CardDescription } from '@/components/ui/card'
import { DURATIONOPTIONS } from '@/features/services/types/constants'
import type { AddServiceDialogProps } from '@/features/services/types/types'
import {
  createService,
  uploadServiceImage,
} from '@/features/services/api/servicesApi'
import {
  serviceSchema,
  type ServicesSchemaValues,
} from '@/features/services/types/schemas'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export function AddServiceDialog({
  siteId,
  services,
  onServiceAdded,
  open,
  setOpen,
}: AddServiceDialogProps) {
  const [loading, setLoading] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [photos, setPhotos] = useState<Record<string, string>>({})
  const [photoCount, setPhotoCount] = useState(0)
  const [error, setError] = useState('')

  const form = useForm<ServicesSchemaValues>({
    resolver: zodResolver(serviceSchema),
    defaultValues: {
      description: '',
      service: '',
      price: '',
      duration: '',
      photos: {},
    },
  })

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

  async function onSubmit(values: ServicesSchemaValues) {
    setLoading(true)
    try {
      await createService({
        site_id: siteId,
        service_id: values.service,
        description: values.description,
        price: values.price,
        duration: values.duration,
        photos: values.photos,
      })

      toast.success('Servicio agregado', {
        description: 'El servicio ha sido agregado exitosamente',
      })

      form.reset()
      setOpen(false)
      onServiceAdded()
    } catch (error: any) {
      toast.error('Error', {
        description:
          error.response?.data?.message ||
          'Ocurrió un error inesperado. Inténtalo de nuevo más tarde.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[425px] max-h-full overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Agregar Nuevo Servicio</DialogTitle>
          <DialogDescription>
            Completa los detalles del servicio que deseas agregar
          </DialogDescription>
        </DialogHeader>
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
            {error.length > 0 && (
              <p className="text-red-500 text-sm self-center">{error}</p>
            )}
            <div className="flex justify-end space-x-4 pt-4">
              <Button
                variant="outline"
                type="button"
                onClick={() => {
                  setOpen(false)
                }}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Agregando...' : 'Agregar Servicio'}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
