// Form schema using zod
import { z } from 'zod'

export const serviceSearchSchema = z.object({
  name: z.string(),
  category_id: z
    .string()
    .transform((val) => Number.parseInt(val))
    .optional(),
  site_id: z
    .string()
    .transform((val) => Number.parseInt(val))
    .optional(),
  service_id: z
    .string()
    .transform((val) => Number.parseInt(val))
    .optional(),
  price: z
    .string()
    .transform((val) => Number.parseInt(val))
    .optional(),
})

export type ServiceSearchSchemaValues = z.infer<typeof serviceSearchSchema>

// Form schema using zod
export const siteSearcSchema = z.object({
  name: z.string(),
  address: z.string(),
})

export type SiteSearchSchemaValues = z.infer<typeof siteSearcSchema>
