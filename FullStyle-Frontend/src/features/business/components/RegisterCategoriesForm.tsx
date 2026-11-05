'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { CATEGORIES } from '@/types/constants'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { Checkbox } from '../../../components/ui/checkbox'
import { assignCategoriesToSite } from '@/features/business/api/businessApi'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../../components/ui/card'
import {
  categorySchema,
  type CategorySchemaValues,
} from '@/features/business/types/schemas'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '../../shared/components/form'

export default function RegisterCategoriesForm({
  urlCallback,
  siteId,
}: {
  urlCallback?: string
  siteId?: string
}) {
  const form = useForm<CategorySchemaValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      items: [1],
    },
  })

  const router = useRouter()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(values: CategorySchemaValues) {
    setError('')
    setLoading(true)
    try {
      const items = values.items
      localStorage.setItem('categories', items.toString())
      if (siteId === undefined) {
        throw new Error('No se ha encontrado el sitio.')
      }
      await assignCategoriesToSite(parseInt(siteId, 10), items)
      if (urlCallback !== undefined) {
        router.push(urlCallback)
      }
    } catch (error: any) {
      if (error.response?.data?.message !== undefined) {
        setError(String(error.response.data.message))
      } else {
        setError('Ocurrió un error inesperado. Inténtalo de nuevo más tarde.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full md:w-auto">
      <CardHeader>
        <CardTitle className="subtitle text-center">
          Registro de categorias
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-y-4"
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              control={form.control}
              name="items"
              render={() => (
                <FormItem>
                  <div className="mb-4 ">
                    <FormDescription className="text-lg">
                      Selecciona las categorias de los servicios que vas a
                      realizar.
                    </FormDescription>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {CATEGORIES.map((item) => (
                      <FormField
                        key={item.id}
                        control={form.control}
                        name="items"
                        render={({ field }) => {
                          return (
                            <FormItem
                              key={item.id}
                              className="flex flex-row items-start space-x-3 space-y-0"
                            >
                              <FormControl>
                                <Checkbox
                                  className="self-center"
                                  checked={field.value?.includes(item.id)}
                                  onCheckedChange={(checked) => {
                                    if (checked === true) {
                                      field.onChange([...field.value, item.id])
                                    } else {
                                      field.onChange(
                                        field.value?.filter(
                                          (value) => value !== item.id,
                                        ),
                                      )
                                    }
                                  }}
                                />
                              </FormControl>
                              <FormLabel className="font-normal text-lg self-center">
                                {item.label}
                              </FormLabel>
                            </FormItem>
                          )
                        }}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            {error.length > 0 && (
              <p className="text-red-500 text-sm">{error}</p>
            )}
            <Button type="submit" className="self-center" disabled={loading}>
              {loading ? 'Registrando...' : 'GUARDAR CATEGORIAS'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
