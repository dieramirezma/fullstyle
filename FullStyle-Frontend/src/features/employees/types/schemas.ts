// Definimos el esquema de validación con Zod
import { z } from 'zod'

export const workerFormSchema = z.object({
  name: z
    .string()
    .min(5, { message: 'El nombre debe tener al menos 5 caracteres.' })
    .max(50, { message: 'El nombre no puede tener más de 50 caracteres.' })
    .refine((val) => /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(val), {
      message: 'El nombre solo puede contener letras y espacios.',
    }),
  description: z
    .string()
    .min(10, { message: 'La descripción debe tener al menos 10 caracteres.' })
    .max(100, { message: 'La descripción tiene un límite de 100 caracteres.' }),
  services: z
    .array(z.number())
    .min(1, { message: 'Debe seleccionar mínimo un servicio' }),
  schedule: z.record(
    z.string(),
    z.object({
      startTime: z.string(),
      endTime: z.string(),
    }),
  ),
  profilepicture: z.string().optional(),
})

export type WorkerFormValues = z.infer<typeof workerFormSchema>

export const userSchema = z.object({
  name: z
    .string({
      error: 'El nombre es obligatorio',
    })
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
      message: 'El nombre solo puede contener letras',
    }),
  description: z
    .string({
      error: 'Los apellidos son obligatorios',
    })
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
      message: 'La descripcion solo puede contener letras',
    }),
})

export type UserSchemaValues = z.infer<typeof userSchema>
