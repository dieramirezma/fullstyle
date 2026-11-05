import {
  createHash,
  createHmac,
  randomUUID,
  timingSafeEqual,
} from 'node:crypto'

export function verifyEvent(
  body: any,
  received: string,
  secret: string,
): boolean {
  if (!secret || !/^[a-f0-9]{64}$/i.test(received)) return false
  try {
    const properties: unknown = body.signature?.properties
    if (
      !Array.isArray(properties) ||
      properties.length < 1 ||
      properties.length > 30 ||
      !Number.isSafeInteger(body.timestamp)
    )
      return false
    const values = properties.map((path: unknown) => {
      if (typeof path !== 'string' || path.length > 200)
        throw new Error('Invalid property')
      let value = body.data
      for (const part of path.split('.')) {
        if (
          ['__proto__', 'prototype', 'constructor'].includes(part) ||
          value === null ||
          typeof value !== 'object' ||
          !Object.prototype.hasOwnProperty.call(value, part)
        )
          throw new Error('Missing property')
        value = value[part]
      }
      if (!['string', 'number', 'boolean'].includes(typeof value))
        throw new Error('Invalid value')
      return String(value)
    })
    const expected = createHash('sha256')
      .update(`${values.join('')}${body.timestamp}${secret}`)
      .digest()
    return timingSafeEqual(expected, Buffer.from(received, 'hex'))
  } catch {
    return false
  }
}

export function eventCapability(body: any, secret: string): string {
  // PyJWT-compatible canonical JSON is ASCII for this provider envelope.
  const encode = (value: unknown): string =>
    Buffer.from(JSON.stringify(value)).toString('base64url')
  const header = encode({ alg: 'HS256', typ: 'JWT' })
  const now = Math.floor(Date.now() / 1000)
  const payload = encode({
    sub: 'fullstyle-next',
    type: 'service',
    aud: 'wompi.receipt',
    iat: now,
    exp: now + 60,
    jti: randomUUID(),
    sha256: createHash('sha256').update(JSON.stringify(body)).digest('hex'),
  })
  return `${header}.${payload}.${createHmac('sha256', secret).update(`${header}.${payload}`).digest('base64url')}`
}
