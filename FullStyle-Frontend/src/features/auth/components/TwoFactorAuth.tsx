'use client'

import { toast } from 'sonner'
import { QRCodeSVG } from 'qrcode.react'
import { useRouter } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import React, { useState } from 'react'
import { Separator } from '@/components/ui/separator'
import { Clipboard, Loader2, Smartphone } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { enable2FA, verify2FA } from '@/features/auth/api/authApi'
import { isRecoveryCodes } from '@/utils/operationContracts'
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from '@/components/ui/input-otp'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export default function TwoFactorAuth() {
  const router = useRouter()
  const [otp, setOtp] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { data: session } = useSession()
  const [otpUrl, setOtpUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([])

  const fetch2FA = async () => {
    if (!session?.user?.email || !password) return
    setIsLoading(true)
    try {
      const res = await enable2FA(session.user.email, password)
      if (res.data.otpauth_url) setOtpUrl(String(res.data.otpauth_url))
    } catch {
      toast.error('No se pudo iniciar MFA. Revisa tu contraseña.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()

    if (!session?.user?.email) {
      setError('Sesión expirada. Por favor, inicia sesión de nuevo.')
      return
    }

    if (!otp || otp.length < 6) {
      setError('Por favor, ingresa el código de verificación de 6 dígitos.')
      return
    }

    setError('')
    setIsVerifying(true)

    try {
      const result = await verify2FA(session.user.email, otp, password)
      const codes: unknown = result.data.recovery_codes
      if (!isRecoveryCodes(codes))
        throw new Error('Códigos de recuperación no disponibles')
      setRecoveryCodes(codes)
      setOtpUrl('')
      setPassword('')
      toast.success('Autenticación en dos factores activada con éxito')
    } catch (err: any) {
      console.error(err)
      const errorMessage =
        typeof err.response?.data?.message === 'string'
          ? err.response.data.message
          : 'Error al verificar el código'
      setError(String(errorMessage))
      toast.error('Error al verificar el código. Por favor, intenta de nuevo.')
    } finally {
      setIsVerifying(false)
    }
  }

  const copyOtpUrl = () => {
    if (otpUrl) {
      navigator.clipboard.writeText(otpUrl)
      toast.success('URL de autenticación copiado al portapapeles')
    }
  }

  const handleCancel = () => {
    const isManager = session?.user?.is_manager
    if (isManager) router.push('/owner')
    else router.push('/customer')
  }

  if (recoveryCodes.length)
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle>Guarda tus códigos de recuperación</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>
            Se muestran una sola vez. Guarda una copia privada fuera de este
            dispositivo. La recuperación exige tu contraseña, elimina el
            autenticador y revoca todas tus sesiones.
          </p>
          <pre className="overflow-auto text-sm">
            {recoveryCodes.join('\n')}
          </pre>
          <Button
            onClick={() => {
              const url = URL.createObjectURL(
                new Blob([recoveryCodes.join('\n')], { type: 'text/plain' }),
              )
              const link = document.createElement('a')
              link.href = url
              link.download = 'fullstyle-recovery-codes.txt'
              link.click()
              URL.revokeObjectURL(url)
            }}
          >
            Descargar códigos
          </Button>
          <Button
            onClick={() => {
              void signOut({ callbackUrl: '/login' })
            }}
          >
            Ya los guardé; iniciar sesión
          </Button>
        </CardContent>
      </Card>
    )

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">
          Autenticación en dos factores
        </CardTitle>
        <CardDescription>
          Mejora la seguridad de tu cuenta con la autenticación en dos factores
        </CardDescription>
      </CardHeader>

      <CardContent>
        <label className="block space-y-2 mb-4">
          <span>Confirma tu contraseña actual</span>
          <Input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value)
            }}
          />
        </label>
        {!otpUrl && (
          <Button onClick={fetch2FA} disabled={!password || isLoading}>
            Iniciar activación MFA
          </Button>
        )}
        {isLoading ? (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2">Generando tu llave secreta.</span>
          </div>
        ) : (
          <>
            {otpUrl ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <h3 className="font-medium">Step 1: Scan QR Code</h3>
                  <p className="text-sm text-muted-foreground">
                    Escanea este código con tu aplicación de autenticación
                    favorita (Google Authenticator, Authy, etc.)
                  </p>
                  <div className="flex justify-center p-4 bg-white rounded-lg">
                    <QRCodeSVG value={otpUrl} size={200} />
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                    onClick={copyOtpUrl}
                  >
                    <Clipboard className="h-4 w-4 mr-2" />
                    Copy Setup Key
                  </Button>
                </div>

                <Separator />

                <form onSubmit={handleVerify} className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="font-medium">
                      Step 2: Enter Verification Code
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Ingresa el número de seis dígitos
                    </p>
                    <div className="flex justify-center py-2">
                      <InputOTP
                        maxLength={6}
                        value={otp}
                        onChange={setOtp}
                        render={({ slots }) => (
                          <InputOTPGroup>
                            {slots.map((slot, index) => (
                              <InputOTPSlot key={index} {...slot} />
                            ))}
                          </InputOTPGroup>
                        )}
                      />
                    </div>
                  </div>

                  {error && (
                    <Alert variant="destructive">
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex gap-2">
                    <Button
                      type="submit"
                      className="w-full"
                      disabled={
                        isVerifying || otp.length < 6 || !otpUrl || !password
                      }
                    >
                      {isVerifying && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Verifica y activa
                    </Button>
                  </div>
                </form>
              </div>
            ) : (
              <div className="py-8 text-center space-y-4">
                <Smartphone className="h-12 w-12 mx-auto text-primary" />
                <p>Ingresa el número de autenticación de tu app</p>

                <form onSubmit={handleVerify} className="space-y-4">
                  <div className="flex justify-center py-2">
                    <InputOTP
                      maxLength={6}
                      value={otp}
                      onChange={setOtp}
                      render={({ slots }) => (
                        <InputOTPGroup>
                          {slots.map((slot, index) => (
                            <InputOTPSlot key={index} {...slot} />
                          ))}
                        </InputOTPGroup>
                      )}
                    />
                  </div>

                  {error && (
                    <Alert variant="destructive">
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={
                      isVerifying || otp.length < 6 || !otpUrl || !password
                    }
                  >
                    {isVerifying && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Verifica el código
                  </Button>
                </form>
              </div>
            )}
          </>
        )}
      </CardContent>

      <CardFooter>
        <Button
          variant="outline"
          className="w-full"
          onClick={handleCancel}
          disabled={isLoading || isVerifying}
        >
          Cancelar
        </Button>
      </CardFooter>
    </Card>
  )
}
