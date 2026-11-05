'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { signIn, getSession } from 'next-auth/react'
import { Input } from '../../../components/ui/input'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { Checkbox } from '../../../components/ui/checkbox'
import { registerCustomer } from '@/features/auth/api/authApi'
import { GoogleIcon } from '../../../components/icons/LogosGoogleIcon'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../../components/ui/card'
import {
  registerUserSchema,
  type RegisterUserSchemaValues,
} from '@/features/auth/types/schemas'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '../../shared/components/form'

export default function RegisterCustomerForm() {
  const form = useForm<RegisterUserSchemaValues>({
    resolver: zodResolver(registerUserSchema),
    defaultValues: {
      names: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  })

  const router = useRouter()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  async function onSubmit(values: RegisterUserSchemaValues) {
    setError('')
    setLoading(true)

    const payload = {
      name: `${values.names.trim()} ${values.lastName.trim()}`,
      email: values.email,
      password: values.password,
    }

    try {
      await registerCustomer(payload)
      router.push('/login')
    } catch (error: any) {
      setError(
        String(error.response?.data?.message) ||
          'Ocurrió un error inesperado. Inténtalo de nuevo más tarde.',
      )
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    try {
      const result = await signIn('google', {
        callbackUrl: '/customer',
        redirect: false,
      })

      if (result?.error) {
        setError('Error al autenticar con Google')
        return
      }

      const session = await getSession()

      if (!session?.user) {
        setError('No se pudo obtener la sesión del usuario')
        return
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}register_google`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: session.user.name,
            email: session.user.email,
          }),
          credentials: 'include',
        },
      )

      if (!response.ok) {
        const error = await response.json()
        setError(`Error en el backend: ${error.error}`)
      }
    } catch (error) {
      console.error('Error al iniciar sesión:', error)
      setError('Ocurrió un error al intentar iniciar sesión con Google')
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="subtitle text-center">Registro cliente</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              name="names"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Nombres<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="lastName"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Apellidos<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="email"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Correo electrónico<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="password"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Contraseña<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showPassword ? 'text' : 'password'}
                        {...field}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={togglePasswordVisibility}
                        aria-label={
                          showPassword
                            ? 'Ocultar contraseña'
                            : 'Mostrar contraseña'
                        }
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-500" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-500" />
                        )}
                      </Button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              name="confirmPassword"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-black">
                    Confirmar Contraseña<span className="text-red-500"> *</span>
                  </FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="acceptPolicy"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel>
                      Acepto la{' '}
                      <Link href="/legal/habeas-data" className="underline">
                        política de tratamiento de datos.
                      </Link>
                      <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormMessage />
                  </div>
                </FormItem>
              )}
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? 'Registrando...' : 'REGISTRARSE'}
            </Button>
            <Button
              variant="outline"
              type="button"
              onClick={handleGoogleSignIn}
            >
              <GoogleIcon />
              CONTINUAR CON GOOGLE
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
