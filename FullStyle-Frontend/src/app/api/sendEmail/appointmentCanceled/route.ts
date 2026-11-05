import { queueLocalEmail } from '@/utils/providerBoundary'

export async function POST(request: Request): Promise<Response> {
  return await queueLocalEmail(request, 'appointmentCanceled')
}
