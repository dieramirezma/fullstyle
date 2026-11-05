'use client'

import axios from 'axios'
import Image from 'next/image'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import GoogleMapComponent from '@/components/map'
import { zodResolver } from '@hookform/resolvers/zod'
import { handleImageUpload } from '@/utils/imagesUpload'
import { MapPin, Loader2, X, ImageIcon } from 'lucide-react'
import { type ResponseGeo } from '@/features/business/types/types'
import { BUSINESSTYPES } from '@/features/business/types/constants'
import { uploadBusinessImage } from '@/features/business/api/businessApi'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  userSchema,
  type UserSchemaValues,
} from '@/features/business/types/schemas'
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

export default function RegisterBusinessForm({
  className,
  urlCallback,
  onRegistrationComplete,
}: {
  className?: string
  urlCallback?: string
  onRegistrationComplete?: (siteId: string) => void
}) {
  const form = useForm<UserSchemaValues>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      name: '',
      address: '',
      phone: '',
      photos: {},
    },
  })

  const router = useRouter()
  const { data: session } = useSession()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showMap, setShowMap] = useState(false)
  const [photoCount, setPhotoCount] = useState(0)
  const [addressLoading, setAddressLoading] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [photos, setPhotos] = useState<Record<string, string>>({})
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(
    null,
  )

  async function handleImageUploadWrapper(
    e: React.ChangeEvent<HTMLInputElement>,
  ) {
    await handleImageUpload(
      e,
      setUploadingImage,
      setError,
      setPhotos,
      form,
      uploadBusinessImage, // or uploadWorkerImage if you want to reuse
      photoCount,
      setPhotoCount,
      'photos',
    )
  }

  function removePhoto(key: string) {
    const newPhotos = Object.fromEntries(
      Object.entries(photos).filter(([k]) => k !== key),
    )
    setPhotos(newPhotos)
    form.setValue('photos', newPhotos)
  }

  async function validateAddress(address: string) {
    setAddressLoading(true)
    setError('')
    setCoords(null)

    try {
      // Append Bogota to the address if not already included
      const fullAddress = address.toLowerCase().includes('bogota')
        ? address
        : `${address}, Bogota`

      const res = await fetch(
        `/api/geocode?address=${encodeURIComponent(fullAddress)}`,
      )
      const data: ResponseGeo = await res.json()

      if (res.ok) {
        setCoords(data.location)
        setShowMap(true)
        form.setValue('address', data.formatted_address)
      } else {
        setError(
          'No se pudo encontrar la dirección. Por favor, verifique e intente nuevamente.',
        )
      }
    } catch (err) {
      setError('Error al validar la dirección')
    } finally {
      setAddressLoading(false)
    }
  }

  async function onSubmit(values: UserSchemaValues) {
    if (!coords) {
      setError('Por favor valide la dirección en el mapa antes de continuar')
      return
    }

    setError('')
    setLoading(true)
    const payload = {
      name: values.name.trim(),
      address: values.address,
      phone: values.phone,
      manager_id: session?.user?.id,
      photos: values.photos,
    }

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}site`,
        payload,
      )
      const siteId = String(response.data.id)
      localStorage.setItem('siteId', siteId)

      if (onRegistrationComplete) {
        onRegistrationComplete(siteId)
      } else {
        router.push(urlCallback ?? '/owner')
      }
    } catch (error: any) {
      if (error.response?.data?.message) {
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
          Registro del Negocio
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              name="name"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Nombre del negocio<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Ej. FullStyle" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              name="address"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Direccion del negocio
                    <span className="text-red-500"> *</span>
                  </FormLabel>
                  <div className="flex gap-2">
                    <FormControl>
                      <Input
                        className="h-auto"
                        {...field}
                        placeholder="Ej: Calle 123 #45-67"
                      />
                    </FormControl>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={async () => {
                        await validateAddress(field.value)
                      }}
                      disabled={!field.value || addressLoading}
                    >
                      {addressLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <MapPin className="h-4 w-4" />
                      )}
                      <span className="ml-2">Validar</span>
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {showMap && coords && (
              <div className="mt-2 rounded-lg overflow-hidden border">
                <GoogleMapComponent position={coords} />
              </div>
            )}

            <FormField
              name="phone"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Número telefónico<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      placeholder="Ej. 3033044340"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="businessType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Tipo de negocio<span className="text-red-500"> *</span>
                  </FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona el tipo de negocio" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {BUSINESSTYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
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
                    Fotos del negocio
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
                            onChange={handleImageUploadWrapper}
                            disabled={uploadingImage}
                          />
                        </label>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Sube una foto de tu negocio para que los clientes puedan
                      verla
                    </p>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {error && <p className="text-red-500 text-sm">{error}</p>}

            <Button type="submit" disabled={loading || !coords}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Registrando...
                </>
              ) : (
                'REGISTRARSE'
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
