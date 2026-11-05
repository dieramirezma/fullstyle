import { z } from 'zod'

export const userSchema = z.object({
  name: z
    .string({
      error: 'Este campo es obligatorio',
    })
    .min(5, {
      message: 'El nombre debe tener al menos 5 caracteres',
    })
    .max(50, {
      message: 'El nombre debe tener máximo 50 caracteres',
    }),
  address: z
    .string({
      error: 'Este campo es obligatorio',
    })
    .min(1, {
      message: 'La direccion es obligatoria',
    }),
  phone: z
    .string({
      error: 'Este campo es obligatorio',
    })
    .min(10, {
      message: 'Debe contener exactamente 10 dígitos',
    })
    .regex(/^[0-9]+$/, {
      message: 'El número telefónico solo puede contener números',
    })
    .max(10, {
      message: 'Debe contener exactamente 10 dígitos',
    })
    .regex(/^3/, {
      message: 'El número telefónico debe empezar por 3',
    }),
  businessType: z.enum(['Barbería', 'Peluquería', 'Salón de estética'], {
    message: 'Seleccione el tipo de negocio',
  }),
  photos: z.record(z.string(), z.string().url()).optional(),
})

export type UserSchemaValues = z.infer<typeof userSchema>

export const categorySchema = z.object({
  items: z.array(z.number()).refine((value) => value.some((item) => item), {
    message: 'Tienes que seleccionar al menos una categoria.',
  }),
})

export type CategorySchemaValues = z.infer<typeof categorySchema>
