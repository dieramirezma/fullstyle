import { z } from 'zod'

export const loginUserSchema = z.object({
  email: z
    .string({
      error: 'El correo electrónico es obligatorio',
    })
    .min(1, {
      message: 'Ingresa el correo',
    }),
  password: z
    .string({
      error: 'La contraseña es obligatoria',
    })
    .min(1, {
      message: 'Ingresa la contraseña',
    }),
})

export type LoginUserSchemaValues = z.infer<typeof loginUserSchema>

export const registerUserSchema = z
  .object({
    names: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(2, {
        message: 'El nombre debe contener como mínimo 2 caracteres',
      })
      .regex(/^[ a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
        message: 'El nombre solo puede contener letras',
      })
      .max(40, {
        message: 'El limite de caracteres es de 40',
      })
      .refine((val) => val.trim().split(' ').length <= 3, {
        message: 'Máximo 3 nombres',
      }),
    lastName: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(3, {
        message: 'El apellido debe contener como mínimo 3 caracteres',
      })
      .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
        message: 'Los apellidos solo pueden contener letras',
      })
      .max(40, {
        message: 'El limite de caracteres es de 40',
      })
      .refine((val) => val.trim().split(' ').length <= 2, {
        message: 'Máximo 2 apellidos',
      }),
    email: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .email({
        message: 'Ingrese un correo válido',
      })
      .max(60, {
        message: 'El límite de caracteres es de 60',
      }),
    password: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(8, {
        message: 'La contraseña debe tener al menos 8 caracteres',
      })
      .regex(/[A-Z]/, {
        message: 'La contraseña debe tener al menos una letra mayúscula',
      })
      .regex(/[\W_]/, {
        message: 'La contraseña debe tener al menos un carácter especial',
      })
      .regex(/[0-9]/, {
        message: 'La contraseña debe tener al menos un número',
      })
      .max(50, {
        message: 'La contraseña debe tener máximo 50 caracteres',
      }),
    confirmPassword: z.string({
      error: 'Debe confirmar la contraseña',
    }),
    acceptPolicy: z
      .boolean({
        error: 'Debes aceptar la política de tratamiento de datos',
      })
      .refine((val) => val, {
        message: 'Debes aceptar la política de tratamiento de datos',
      }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Las contraseñas no coinciden',
  })

export type RegisterUserSchemaValues = z.infer<typeof registerUserSchema>

export const registerOwnerSchema = z
  .object({
    name: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(2, {
        message: 'El nombre debe contener como mínimo 2 caracteres',
      })
      .regex(/^[ a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
        message: 'El nombre solo puede contener letras',
      })
      .max(40, {
        message: 'El limite de caracteres es de 40',
      })
      .refine((val) => val.trim().split(' ').length <= 3, {
        message: 'Máximo 3 nombres',
      }),
    lastName: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(3, {
        message: 'El apellido debe contener como mínimo 3 caracteres',
      })
      .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
        message: 'Los apellidos solo pueden contener letras',
      })
      .max(40, {
        message: 'El limite de caracteres es de 40',
      })
      .refine((val) => val.trim().split(' ').length <= 2, {
        message: 'Máximo 2 apellidos',
      }),
    email: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .email({
        message: 'Ingrese un correo válido',
      })
      .max(60, {
        message: 'El límite de caracteres es de 60',
      }),
    phone: z
      .string({
        error: 'El número telefónico es obligatorio',
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
    password: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .min(8, {
        message: 'La contraseña debe tener al menos 8 caracteres',
      })
      .regex(/[A-Z]/, {
        message: 'La contraseña debe tener al menos una letra mayúscula',
      })
      .regex(/[\W_]/, {
        message: 'La contraseña debe tener al menos un carácter especial',
      })
      .regex(/[0-9]/, {
        message: 'La contraseña debe tener al menos un número',
      })
      .max(50, {
        message: 'La contraseña debe tener máximo 50 caracteres',
      }),
    confirmPassword: z.string({
      error: 'Debe confirmar la contraseña',
    }),
    bankName: z.enum(
      ['Bancolombia', 'Caja Social', 'Banco de Bogota', 'Mundo mujer'],
      {
        message: 'Seleccione su banco',
      },
    ),
    bankAcountType: z.enum(['Ahorros', 'Corriente'], {
      message: 'Seleccione su tipo de cuenta',
    }),
    accountNumber: z
      .string({
        error: 'Este campo es obligatorio',
      })
      .regex(/^[0-9]+$/, {
        message: 'El número de cuenta solo puede contener números',
      })
      .min(11, {
        message: 'El número de cuenta debe contener como minimo 11 dígitos',
      })
      .max(19, {
        message: 'El número de cuenta debe contener como maximo 19 dígitos',
      }),
    accountOwner: z
      .string({
        error: 'El nombre del titular es obligatorio',
      })
      .min(6, {
        message: 'El nombre del titular debe contener como mínimo 6 caracteres',
      })
      .max(99, {
        message: 'El limite de caracteres es de 99',
      })
      .regex(/^[ a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, {
        message: 'El nombre solo puede contener letras',
      }),
    acceptPolicy: z
      .boolean({
        error: 'Debes aceptar la política de tratamiento de datos',
      })
      .refine((val) => val, {
        message: 'Debes aceptar la política de tratamiento de datos',
      }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Las contraseñas no coinciden',
  })

export type RegisterOwnerSchemaValues = z.infer<typeof registerOwnerSchema>

export const resetPasswordSchema = z
  .object({
    password: z
      .string({
        error: 'La contraseña es obligatoria',
      })
      .min(8, {
        message: 'La contraseña debe tener al menos 8 caracteres',
      })
      .max(50, {
        message: 'La contraseña debe tener máximo 50 caracteres',
      }),
    confirmPassword: z.string({
      error: 'Debe confirmar la contraseña',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Las contraseñas no coinciden',
  })

export type ResetPasswordSchemaValues = z.infer<typeof resetPasswordSchema>

export const resetPasswordRequestSchema = z.object({
  email: z
    .string({
      error: 'El correo electrónico es obligatorio',
    })
    .email({
      message: 'Ingrese un correo válido',
    }),
})

export type ResetPasswordRequestSchemaValues = z.infer<
  typeof resetPasswordRequestSchema
>
