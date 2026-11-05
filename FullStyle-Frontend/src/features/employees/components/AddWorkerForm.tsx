'use client'

import Image from 'next/image'
import { toast } from 'sonner'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { ImageIcon, Loader2, X } from 'lucide-react'
import { zodResolver } from '@hookform/resolvers/zod'
import { TimeRangeInput } from '@/components/TimeRangeInput'
import { DAYS, SCHEDULE } from '@/features/employees/types/constants'
import { type AddWorkerDialogProps } from '@/features/employees/types/types'
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
  createWorker,
  assignWorkerServices,
  assignWorkerSchedule,
} from '@/features/employees/api/workerApi'

const AddWorkerForm = ({
  siteId,
  services,
  onWorkerAdded,
  setOpen,
  ...props
}: AddWorkerDialogProps) => {
  const [loading, setLoading] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [photos, setPhotos] = useState<string>('')
  const [error, setError] = useState('')

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
        site_id: siteId,
        description: data.description,
        services: data.services,
        profilepicture: photos,
      })

      // Asignar servicios
      await assignWorkerServices(workerId, data.services)

      // Asignar horarios
      await assignWorkerSchedule(workerId, data.schedule)

      toast.success('Éxito', {
        description: 'Trabajador agregado correctamente',
      })

      onWorkerAdded()
      setOpen(false)
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
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Nombre del trabajador<span className="text-red-500"> *</span>
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
              startTime={form.getValues().schedule[day]?.startTime || '10:00'}
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
                                        (value) => value !== service.service_id,
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
              <FormLabel className="font-black">Foto del trabajador</FormLabel>
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
            {loading ? 'Agregando...' : 'Agregar Trabajador'}
          </Button>
        </div>
      </form>
    </Form>
  )
}

export default AddWorkerForm
