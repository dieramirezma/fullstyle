import { z } from 'zod'
import { DURATIONOPTIONS } from '@/features/services/types/constants'

export const serviceSchema = z.object({
  description: z
    .string({
      error: 'Este campo es requerido',
    })
    .min(10, {
      message: 'La descripción debe tener al menos 10 caracteres',
    })
    .max(100, {
      message: 'La descripción tiene un limite de 100 caracteres',
    })
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ,.?¿!¡)(\s]+$/, {
      message:
        'La descripción solo puede contener letras y signos de puntuación',
    }),
  service: z
    .string({
      error: 'Selecciona un servicio',
    })
    .min(1, {
      message: 'Selecciona un servicio',
    }),
  price: z
    .string({
      error: 'Indica el precio de tu servicio',
    })
    .refine((val) => Number(val) > 1000, {
      message: 'El precio debe ser mayor a 1000 COP',
    })
    .refine((val) => Number(val) % 50 === 0, {
      message: 'El precio debe ser múltiplo de 50 COP',
    }),
  duration: z.enum(
    DURATIONOPTIONS.map((option) => option.value) as [string, ...string[]],
    {
      message: 'Selecciona una duración',
    },
  ),
  photos: z.record(z.string(), z.string().url()).optional(),
})

export type ServicesSchemaValues = z.infer<typeof serviceSchema>

export const userSchema = z.object({
  description: z
    .string({
      error: 'Este campo es requerido',
    })
    .min(10, {
      message: 'La descripción debe tener al menos 10 caracteres',
    })
    .max(100, {
      message: 'La descripción tiene un limite de 100 caracteres',
    })
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ,.?¿!¡)(\s]+$/, {
      message:
        'La descripción solo puede contener letras y signos de puntuación',
    }),
  service: z
    .string({
      error: 'Selecciona un servicio',
    })
    .min(1, {
      message: 'Selecciona un servicio',
    }),
  price: z
    .string({
      error: 'Indica el precio de tu servicio',
    })
    .refine((val) => Number(val) > 1000, {
      message: 'El precio debe ser mayor a 1000 COP',
    })
    .refine((val) => Number(val) % 50 === 0, {
      message: 'El precio debe ser múltiplo de 50 COP',
    }),
  duration: z.enum(
    DURATIONOPTIONS.map((option) => option.value) as [string, ...string[]],
    {
      message: 'Selecciona una duración',
    },
  ),
  photos: z.record(z.string(), z.string().url()).optional(),
})

export type UserSchemaValues = z.infer<typeof userSchema>
