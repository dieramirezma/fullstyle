import { providerContext } from '@/utils/providerBoundary'
import { storeImage } from '@/utils/localMedia'

export async function POST(request: Request): Promise<Response> {
  const context = await providerContext(request, 'upload')
  if (context.error) return context.error
  if (Number(request.headers.get('content-length') ?? 0) > 1100000)
    return Response.json({ error: 'Image too large' }, { status: 413 })
  try {
    const body = await request.formData()
    const image = body.get('image')
    if (!(image instanceof File))
      return Response.json({ error: 'Image required' }, { status: 400 })
    const url = await storeImage(context.user.id, image)
    return Response.json({ success: true, url, mode: 'local' })
  } catch {
    return Response.json(
      { error: 'Invalid image; PNG/JPEG, maximum 1 MiB' },
      { status: 400 },
    )
  }
}
