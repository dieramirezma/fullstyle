'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Input } from '../../../components/ui/input'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { Checkbox } from '../../../components/ui/checkbox'
import { registerOwner } from '@/features/auth/api/authApi'
import { BANK_ACCOUNT_TYPES, BANK_NAMES } from '@/features/auth/types/constants'
import {
  registerOwnerSchema,
  type RegisterOwnerSchemaValues,
} from '@/features/auth/types/schemas'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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

export default function RegisterOwnerForm() {
  const form = useForm<RegisterOwnerSchemaValues>({
    resolver: zodResolver(registerOwnerSchema),
    defaultValues: {
      name: '',
      lastName: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      accountNumber: '',
      accountOwner: '',
    },
  })

  const router = useRouter()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  async function onSubmit(values: RegisterOwnerSchemaValues) {
    setError('')
    setLoading(true)

    const payload = {
      name: `${values.name.trim()} ${values.lastName.trim()}`,
      email: values.email,
      password: values.password,
      bankaccount: values.accountNumber,
      accounttype: values.bankAcountType,
      bankentity: values.bankName,
    }

    try {
      const response = await registerOwner(payload)
      localStorage.setItem('userId', String(response.data.user.id))
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

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="subtitle self-center">
          Registro de Nuevo Administrador
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <CardDescription className="text-xl text-black ">
              Datos personales
            </CardDescription>
            <div className="grid md:grid-cols-2 gap-4 grid-cols-1">
              <FormField
                name="name"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Nombres<span className="text-red-500"> *</span>
                    </FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Ej. José Ricardo" />
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
                      <Input {...field} placeholder="Ej. Perez Puentes" />
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
                      <Input
                        {...field}
                        placeholder="Ej. tucorreo@example.com"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="phone"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Número telefónico<span className="text-red-500"> *</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        placeholder="Ej. 3033044340"
                      />
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
                          placeholder="••••••••"
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
                      Confirmar Contraseña
                      <span className="text-red-500"> *</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        {...field}
                        placeholder="••••••••"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <CardDescription className="text-xl text-black">
              Datos bancarios
            </CardDescription>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="bankName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Nombre de la entidad
                      <span className="text-red-500"> *</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecciona una entidad bancaria" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {BANK_NAMES.map((bank) => (
                          <SelectItem key={bank} value={bank}>
                            {bank}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="bankAcountType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Tipo de cuenta<span className="text-red-500"> *</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecciona el tipo de cuenta" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {BANK_ACCOUNT_TYPES.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="accountNumber"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Número de cuenta<span className="text-red-500"> *</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        placeholder="Ej. 546653234548"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="accountOwner"
                control={form.control}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="font-black">
                      Nombre del titular<span className="text-red-500"> *</span>
                    </FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="Ej. José Perez" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
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
                        política de tratamiento de datos
                      </Link>{' '}
                      <span className="text-red-500">*</span>
                    </FormLabel>
                    <FormMessage />
                  </div>
                </FormItem>
              )}
            />
            {error.length > 0 && (
              <p className="text-red-500 text-sm">{error}</p>
            )}
            <Button
              type="submit"
              className="w-1/2 self-center"
              disabled={loading}
            >
              {loading ? 'Registrando...' : 'REGISTRARSE'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
