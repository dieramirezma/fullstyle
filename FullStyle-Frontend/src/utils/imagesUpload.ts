export async function handleImageUpload(
  e: React.ChangeEvent<HTMLInputElement>,
  setUploadingImage: (v: boolean) => void,
  setError: (v: string) => void,
  setPhotos: (v: Record<string, string>) => void,
  form: any,
  uploadFn: (file: File) => Promise<string>,
  photoCount: number,
  setPhotoCount: (fn: (prev: number) => number) => void,
  fieldName: string = 'photos',
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
    const url = await uploadFn(file)
    const photoKey = `photo${photoCount + 1}`
    const existingPhotos =
      (form.getValues(fieldName) as Record<string, string>) || {}
    const newPhotos: Record<string, string> = {
      ...existingPhotos,
      [photoKey]: url,
    }
    setPhotos(newPhotos)
    setPhotoCount((prev) => prev + 1)
    form.setValue(fieldName, newPhotos)
  } catch (err: any) {
    setError(
      'Error al subir la imagen: ' + (err.message || 'Error desconocido'),
    )
  } finally {
    setUploadingImage(false)
    e.target.value = ''
  }
}
