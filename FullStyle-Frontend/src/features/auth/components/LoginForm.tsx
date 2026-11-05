'use client'

import Link from 'next/link'
import { toast } from 'sonner'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Input } from '../../../components/ui/input'
import { getSession, signIn } from 'next-auth/react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { GoogleIcon } from '../../../components/icons/LogosGoogleIcon'
import {
  loginUserSchema,
  type LoginUserSchemaValues,
} from '@/features/auth/types/schemas'
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

export default function LoginForm() {
  const [error, setError] = useState('')
  const [otp, setOtp] = useState('')
  const [recover, setRecover] = useState(false)
  const [recoveryCode, setRecoveryCode] = useState('')
  // const recaptchaRef = useRef<ReCAPTCHA>(null)
  const [loading, setLoading] = useState(false)
  // const [isVerified, setIsVerified] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const router = useRouter()
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  const form = useForm<LoginUserSchemaValues>({
    resolver: zodResolver(loginUserSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = async (values: LoginUserSchemaValues) => {
    setLoading(true)
    setError('')
    try {
      if (recover) {
        const response = await fetch('/api/logic/mfa/recover', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...values, recovery_code: recoveryCode }),
        })
        if (!response.ok) throw new Error('Recovery rejected')
        setRecover(false)
        setRecoveryCode('')
        setOtp('')
        toast.success(
          'Autenticador eliminado y sesiones revocadas. Inicia sesión y activa MFA nuevamente.',
        )
        return
      }
      const res = await signIn('credentials', {
        redirect: false,
        email: values.email,
        password: values.password,
        otp,
      })

      if (res?.error != null) {
        console.log('Error:', res.error)
        setError('Credenciales inválidas')
      } else {
        const session = await getSession()

        toast.success('Éxito', {
          description: 'Inicio de sesión exitoso',
        })
        if (session?.user) {
          const isManager = (session.user as any).is_manager
          router.push(isManager ? '/owner' : '/customer')
        }
      }
    } catch (err) {
      setError('Error al iniciar sesión. Inténtalo de nuevo')
      toast.error('Error al iniciar sesión', {
        description: 'Inténtalo de nuevo',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await signIn('google', {
        callbackUrl: '/customer',
        redirect: false,
        prompt: 'login',
      })

      if (result?.error != null) {
        throw new Error('Error al iniciar sesión con Google')
      }
    } catch (error) {
      setError('Ocurrió un error al iniciar sesión con Google')
      toast.error('Error', {
        description: 'Ocurrió un error al iniciar sesión con Google',
      })
    } finally {
      setLoading(false)
    }
  }

  // async function handleCaptchaSubmission(token: string | null) {
  //   try {
  //     if (token) {
  //       await fetch('/api/recaptcha', {
  //         method: 'POST',
  //         headers: {
  //           Accept: 'application/json',
  //           'Content-Type': 'application/json',
  //         },
  //         body: JSON.stringify({ token }),
  //       })
  //       setIsVerified(true)
  //     }
  //   } catch (e) {
  //     setIsVerified(false)
  //   }
  // }

  // const handleChange = (token: string | null) => {
  //   handleCaptchaSubmission(token)
  // }

  // function handleExpired() {
  //   setIsVerified(false)
  // }

  return (
    <Card className="w-full shadow-lg">
      <CardHeader className="space-y-2">
        <CardTitle className="subtitle self-center">Iniciar Sesión</CardTitle>
        <CardDescription className="text-center">
          Ingresa tu correo y contraseña para iniciar
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              name="email"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="font-semibold">
                    Correo electrónico
                  </FormLabel>
                  <FormControl>
                    <Input {...field} className="w-full" />
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
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <FormLabel className="font-semibold">
                        Contraseña
                      </FormLabel>
                      <Link
                        href="/password_reset"
                        className="text-sm text-muted-foreground hover:text-primary underline underline-offset-4"
                      >
                        ¿Olvidaste tu contraseña?
                      </Link>
                    </div>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? 'text' : 'password'}
                          {...field}
                          className="w-full pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={togglePasswordVisibility}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </div>
                </FormItem>
              )}
            />
            <label className="block space-y-2">
              <span>Código de autenticación (si activaste MFA)</span>
              <Input
                value={otp}
                onChange={(event) => {
                  setOtp(event.target.value)
                }}
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
              />
            </label>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setRecover(!recover)
              }}
            >
              {recover ? 'Volver al inicio de sesión' : 'Perdí mi autenticador'}
            </Button>
            {recover && (
              <label className="block space-y-2">
                <span>Código de recuperación guardado</span>
                <Input
                  value={recoveryCode}
                  autoComplete="off"
                  onChange={(event) => {
                    setRecoveryCode(event.target.value)
                  }}
                />
              </label>
            )}
            {error && (
              <p className="text-sm font-medium text-destructive">{error}</p>
            )}
            <div className="text-center text-sm">
              ¿No tienes cuenta?{' '}
              <Link href="/register" className="underline underline-offset-4">
                ¡Registrate!
              </Link>
            </div>
            <div className="flex justify-center">
              {/* <ReCAPTCHA
                sitekey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY ?? ''}
                ref={recaptchaRef}
                onChange={handleChange}
                onExpired={handleExpired}
              /> */}
            </div>
            <div className="space-y-3">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading
                  ? 'Cargando...'
                  : recover
                    ? 'Recuperar acceso'
                    : 'Iniciar Sesión'}
              </Button>
              <Button
                variant="outline"
                type="button"
                className="w-full"
                onClick={handleGoogleSignIn}
              >
                <GoogleIcon className="mr-2 h-5 w-5" />
                Iniciar con Google
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
