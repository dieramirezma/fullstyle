export function GET(): Response {
  return Response.json({ status: 'ok', mode: 'local' })
}
