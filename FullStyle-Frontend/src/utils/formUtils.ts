import { DAYS } from '@/features/employees/types/constants'
import { uploadWorkerImage } from '@/features/employees/api/workerApi'
import { type WorkerFormValues } from '@/features/employees/types/schemas'

export const resetForm = (form: any) => {
  form.reset({
    name: '',
    description: '',
    services: [],
    schedule: DAYS.reduce(
      (acc, day) => ({
        ...acc,
        [day]: { startTime: '10:00', endTime: '19:00' },
      }),
      {},
    ),
    profilepicture: '',
  })
}

export const handleTimeChange = (
  form: any,
  day: string,
  startTime: string,
  endTime: string,
) => {
  const currentSchedule = form.getValues('schedule')
  form.setValue(
    'schedule',
    {
      ...currentSchedule,
      [day]: { startTime, endTime },
    },
    { shouldValidate: true },
  )
}

export const timeValidation = (data: WorkerFormValues) => {
  for (const day of DAYS) {
    const { startTime, endTime } = data.schedule[day]
    if (startTime.length > 0 && endTime.length > 0 && startTime >= endTime) {
      throw new Error(
        `Para ${day}, la hora de fin debe ser posterior a la hora de inicio.`,
      )
    }
  }
}

export async function handleWorkerImageUpload(
  e: React.ChangeEvent<HTMLInputElement>,
  setUploadingImage: (v: boolean) => void,
  setError: (v: string) => void,
  setPhotos: (v: string) => void,
  form: any, // You can type this more strictly if you want
) {
  const file = e.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    setError('El archivo debe ser una imagen')
    return
  }

  setUploadingImage(true)
  setError('')

  try {
    const url = await uploadWorkerImage(file)
    setPhotos(url)
    form.setValue('profilepicture', url)
  } catch (err: any) {
    setError(
      'Error al subir la imagen: ' + (err.message || 'Error desconocido'),
    )
  } finally {
    setUploadingImage(false)
    e.target.value = ''
  }
}
