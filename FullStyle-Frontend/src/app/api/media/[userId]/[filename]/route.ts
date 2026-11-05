import { providerContext } from '@/utils/providerBoundary'
import { loadImage } from '@/utils/localMedia'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ userId: string; filename: string }> },
): Promise<Response> {
  const context = await providerContext(request, 'upload')
  if (context.error) return context.error
  const target = await params
  if (Number(target.userId) !== context.user.id)
    return new Response(null, { status: 404 })
  try {
    const bytes = await loadImage(context.user.id, target.filename)
    return new Response(new Uint8Array(bytes), {
      headers: {
        'Content-Type': target.filename.endsWith('.png')
          ? 'image/png'
          : 'image/jpeg',
        'Cache-Control': 'private, no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    })
  } catch {
    return new Response(null, { status: 404 })
  }
}
