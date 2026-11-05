'use client'

import Link from 'next/link'
import { toast } from 'sonner'
import Image from 'next/image'
import { useForm } from 'react-hook-form'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { ImageIcon, Loader2, X } from 'lucide-react'
import { zodResolver } from '@hookform/resolvers/zod'
import { TimeRangeInput } from '@/components/TimeRangeInput'
import { type Service } from '@/features/employees/types/types'
import { DAYS, SCHEDULE } from '@/features/employees/types/constants'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import {
  workerFormSchema,
  type WorkerFormValues,
} from '@/features/employees/types/schemas'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/features/shared/components/form'
import {
  handleTimeChange,
  handleWorkerImageUpload,
  resetForm,
  timeValidation,
} from '@/utils/formUtils'
import {
  assignWorkerSchedule,
  assignWorkerServices,
  createWorker,
  fetchServicesBySite,
  fetchSiteByManager,
} from '@/features/employees/api/workerApi'

const WorkerScheduleForm = ({
  className,
  urlCallback,
}: {
  className?: string
  urlCallback?: string
}) => {
  const [loading, setLoading] = useState(false)
  const [services, setServices] = useState<Service[]>([])
  const [siteId, setSiteId] = useState<number | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [photos, setPhotos] = useState<string>('')
  const [error, setError] = useState('')

  const { data: session } = useSession()
  const router = useRouter()

  useEffect(() => {
    const fetchSiteAndServices = async () => {
      if (session?.user.id) {
        try {
          const site = await fetchSiteByManager(session.user.id)
          const siteId = site?.id as number
          setSiteId(siteId)

          try {
            const servicesData = await fetchServicesBySite(siteId)
            setServices(servicesData)
          } catch (error) {
            console.log(error)
          }
        } catch (error) {
          console.log(error)
        } finally {
          setLoading(false)
        }
      }
    }

    fetchSiteAndServices()
  }, [session?.user.id])

  // Inicializamos el formulario con React Hook Form y Zod
  const form = useForm<WorkerFormValues>({
    resolver: zodResolver(workerFormSchema),
    defaultValues: {
      name: '',
      description: '',
      services: [],
      schedule: SCHEDULE,
      profilepicture: '',
    },
  })

  async function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    await handleWorkerImageUpload(
      e,
      setUploadingImage,
      setError,
      setPhotos,
      form,
    )
  }

  function removePhoto() {
    setPhotos('')
    form.setValue('profilepicture', '')
  }

  const onSubmit = async (data: WorkerFormValues) => {
    setLoading(true)

    try {
      // Validación adicional para las horas
      timeValidation(data)

      // Crear trabajador
      const workerId = await createWorker({
        name: data.name,
        site_id: siteId ?? 0,
        description: data.description,
        services: data.services,
        profilepicture: photos,
      })

      // Asignar servicios
      await assignWorkerServices(workerId, data.services)

      // Asignar horarios
      await assignWorkerSchedule(workerId, data.schedule)

      if (urlCallback) {
        router.push(urlCallback)
      }

      toast.success('Éxito', {
        description: 'Trabajador agregado correctamente',
      })

      resetForm(form)
    } catch (error: any) {
      toast.error('Error', {
        description:
          error.response?.data?.message ||
          error.message ||
          'Ocurrió un error inesperado',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className={className ?? 'w-full max-w-2xl mx-auto'}>
      <CardHeader>
        <CardTitle className="subtitle text-center">
          Registro de Trabajador y Horario
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Nombre del trabajador
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
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Descripción<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Textarea {...field} rows={3} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <Label>
                Horario de trabajo<span className="text-red-500"> *</span>
              </Label>
              {DAYS.map((day) => (
                <TimeRangeInput
                  key={day}
                  day={day}
                  startTime={
                    form.getValues().schedule[day]?.startTime || '10:00'
                  }
                  endTime={form.getValues().schedule[day]?.endTime || '19:00'}
                  onChange={(startTime, endTime) => {
                    handleTimeChange(form, day, startTime, endTime)
                  }} // Have doubts about this line
                />
              ))}
            </div>

            <FormField
              control={form.control}
              name="services"
              render={() => (
                <FormItem>
                  <div className="mb-4">
                    <FormLabel>
                      Servicios que realizará
                      <span className="text-red-500"> *</span>
                    </FormLabel>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {services.map((service) => (
                      <FormField
                        key={service.service_id}
                        control={form.control}
                        name="services"
                        render={({ field }) => {
                          return (
                            <FormItem
                              key={service.service_id}
                              className="flex flex-row items-start space-x-3 space-y-0"
                            >
                              <FormControl>
                                <Checkbox
                                  checked={field.value?.includes(
                                    service.service_id,
                                  )}
                                  onCheckedChange={(checked) => {
                                    checked
                                      ? field.onChange([
                                          ...field.value,
                                          service.service_id,
                                        ])
                                      : field.onChange(
                                          field.value?.filter(
                                            (value) =>
                                              value !== service.service_id,
                                          ),
                                        )
                                  }}
                                />
                              </FormControl>
                              <FormLabel className="font-normal">
                                {service.service_name}
                              </FormLabel>
                            </FormItem>
                          )
                        }}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="profilepicture"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Foto del trabajador
                  </FormLabel>
                  <div className="space-y-4">
                    <div className="flex flex-wrap gap-4">
                      {photos && (
                        <div className="relative w-24 h-24 rounded-md overflow-hidden border">
                          <Image
                            src={photos || '/placeholder.svg'}
                            alt={'Foto perfil'}
                            fill
                            className="object-cover"
                          />
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            className="absolute top-1 right-1 h-6 w-6"
                            onClick={() => {
                              removePhoto()
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      )}

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
                      Sube una foto de tu trabajador para que los clientes lo
                      reconozcan
                    </p>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {error.length > 0 && (
              <p className="text-red-500 text-sm self-center">{error}</p>
            )}
            <CardFooter className="flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-y-0 sm:space-x-4">
              <Button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto"
              >
                {loading ? 'Agregando...' : 'AGREGAR TRABAJADOR'}
              </Button>
              {!urlCallback && (
                <Button variant="outline" className="w-full sm:w-auto">
                  <Link href="/login" className="w-full">
                    Finalizar registro
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

export default WorkerScheduleForm
