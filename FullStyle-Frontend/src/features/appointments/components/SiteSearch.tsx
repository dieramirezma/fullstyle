'use client'

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from '@/features/shared/components/form'

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

import { useState } from 'react'
import { Filter, X } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { useSearch } from '@/context/search-context'
import { Input } from '../../../components/ui/input'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import { searchSites } from '@/features/appointments/api/appointmentApi'
import { type SiteSearchSchemaValues, siteSearcSchema } from '../types/schemas'

function SiteSearch() {
  // const [services, setServices] = useState<Service[]>([])
  const { setSites } = useSearch()
  const [isOpen, setIsOpen] = useState(false)

  // Form hook
  const form = useForm<SiteSearchSchemaValues>({
    resolver: zodResolver(siteSearcSchema),
    defaultValues: {
      name: '',
      address: '',
    },
  })

  // Action when the form is submitted
  async function onSubmit(values: SiteSearchSchemaValues) {
    try {
      const data = await searchSites({
        name: values.name,
        address: values.address,
      })
      setSites(data)
      setIsOpen(false)
    } catch (error) {
      setSites([])
      setIsOpen(false)
    }
  }

  const handleReset = () => {
    form.reset()
  }

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" />
          Filtros
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Filtrar sitios de estética</SheetTitle>
        </SheetHeader>
        <div className="mt-4">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <Input placeholder="Nombre del sitio" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <Input placeholder="Dirección" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  type="button"
                  onClick={handleReset}
                  className="flex-1"
                >
                  <X className="h-4 w-4 mr-2" />
                  Limpiar
                </Button>
                <Button type="submit" className="flex-1">
                  Buscar
                </Button>
              </div>
            </form>
          </Form>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export default SiteSearch
