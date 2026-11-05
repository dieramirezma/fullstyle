'use client'

import Link from 'next/link'
import { toast } from 'sonner'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Input } from '../../../components/ui/input'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { requestPasswordReset } from '@/features/auth/api/authApi'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../../components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '../../shared/components/form'
import {
  type ResetPasswordRequestSchemaValues,
  resetPasswordRequestSchema,
} from '@/features/auth/types/schemas'

export default function ResetPasswordRequest() {
  const form = useForm<ResetPasswordRequestSchemaValues>({
    resolver: zodResolver(resetPasswordRequestSchema),
    defaultValues: {
      email: '',
    },
  })

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(values: ResetPasswordRequestSchemaValues) {
    setError('')
    setLoading(true)

    try {
      await requestPasswordReset(values.email)
      toast.success('Correo enviado', {
        description:
          'Hemos enviado un correo con instrucciones para reestablecer tu contraseña.',
      })
    } catch (error: any) {
      toast.error('Error', {
        description:
          'No se pudo enviar el correo de reestablecimiento de contraseña. Por favor, intenta de nuevo.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="subtitle text-center">
          Reestablece tu contraseña
        </CardTitle>
        <CardDescription>
          Ingresa tu correo para enviarte un enlace de reestablecimiento de
          contraseña
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              name="email"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Correo electrónico
                  </FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Link
              href="/login"
              className="text-center inline-block text-sm underline-offset-4 hover:underline"
            >
              Volver a iniciar sesión
            </Link>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? 'Enviando...' : 'Envía correo de recuperación'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
