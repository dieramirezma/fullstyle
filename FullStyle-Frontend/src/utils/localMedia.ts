import { randomUUID } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = '/tmp/fullstyle-media'

export async function storeImage(userId: number, file: File): Promise<string> {
  if (process.env.LOCAL_RUNTIME !== 'true')
    throw new Error('Local storage disabled')
  if (file.size > 1048576) throw new Error('Image exceeds 1 MiB')
  const bytes = Buffer.from(await file.arrayBuffer())
  const png = bytes
    .subarray(0, 8)
    .equals(Buffer.from('89504e470d0a1a0a', 'hex'))
  const jpeg =
    bytes.length > 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255
  const extension =
    png && file.type === 'image/png'
      ? 'png'
      : jpeg && file.type === 'image/jpeg'
        ? 'jpg'
        : ''
  if (!extension)
    throw new Error('Only PNG/JPEG with matching signature accepted')
  const filename = `${randomUUID()}.${extension}`
  const directory = path.join(root, String(userId))
  await mkdir(directory, { recursive: true })
  await writeFile(path.join(directory, filename), bytes, { flag: 'wx' })
  return `/api/media/${userId}/${filename}`
}

export async function loadImage(
  userId: number,
  filename: string,
): Promise<Buffer> {
  if (!/^[a-f0-9-]{36}\.(png|jpg)$/.test(filename))
    throw new Error('Invalid media ID')
  return await readFile(path.join(root, String(userId), filename))
}
