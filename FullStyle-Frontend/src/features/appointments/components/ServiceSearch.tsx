'use client'

import axios from 'axios'
import { type z } from 'zod'
import { toast } from 'sonner'
import { Filter, X } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { useEffect, useState } from 'react'
import { PRICES } from '../types/constants'
import { useSearch } from '@/context/search-context'
import { Input } from '../../../components/ui/input'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '../../../components/ui/button'
import {
  serviceSearchSchema,
  type ServiceSearchSchemaValues,
} from '../types/schemas'
import {
  type Category,
  type ErrorMessage,
  type Service,
  type Site,
} from '../types/types'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  fetchAllServices,
  fetchAllCategories,
  fetchSitesByService,
} from '@/features/appointments/api/appointmentApi'

function ServiceSearch() {
  const { fetchServices } = useSearch()
  const [isOpen, setIsOpen] = useState(false)
  const [sites, setSites] = useState<Site[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  // Form hook
  const form = useForm<
    z.input<typeof serviceSearchSchema>,
    unknown,
    ServiceSearchSchemaValues
  >({
    resolver: zodResolver(serviceSearchSchema),
    defaultValues: {
      name: '',
      category_id: undefined,
      site_id: undefined,
      service_id: undefined,
      price: undefined,
    },
  })

  // Action when the form is submitted
  async function onSubmit(values: ServiceSearchSchemaValues) {
    try {
      fetchServices(1, values)
      setIsOpen(false)
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const response = error.response
        const data: ErrorMessage = response?.data
        toast.error('Error al buscar servicios: ' + data.message)
      }
      setIsOpen(false)
    }
  }

  // Fetch services, categories and sites from the API when the component is mounted
  useEffect(() => {
    const fetchServicesData = async () => {
      setServices((await fetchAllServices()) as Service[])
      setCategories((await fetchAllCategories()) as Category[])
      setSites(await fetchSitesByService('')) // or another function if you want all sites
    }
    fetchServicesData()
  }, [])

  const handleReset = () => {
    form.reset({
      name: '',
      category_id: undefined,
      site_id: undefined,
      service_id: undefined,
      price: undefined,
    })

    // Realizar una búsqueda sin filtros
    onSubmit({
      name: '',
      category_id: undefined,
      site_id: undefined,
      service_id: undefined,
      price: undefined,
    })
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
          <SheetTitle>Filtrar Servicios</SheetTitle>
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
                      <Input placeholder="Nombre del servicio" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="category_id"
                render={({ field }) => (
                  <FormItem className="w-full">
                    <Select
                      onValueChange={field.onChange}
                      value={field.value != null ? field.value.toString() : ''}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Categoría" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="max-h-64">
                        {categories.map((category) => (
                          <SelectItem
                            key={category.id}
                            value={category.id.toString()}
                          >
                            {category.name}
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
                name="site_id"
                render={({ field }) => (
                  <FormItem className="w-full">
                    <Select
                      onValueChange={field.onChange}
                      value={field.value != null ? field.value.toString() : ''}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Sitio" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="max-h-64">
                        {sites.map((site) => (
                          <SelectItem key={site.id} value={site.id.toString()}>
                            {site.name}
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
                name="service_id"
                render={({ field }) => (
                  <FormItem className="w-full">
                    <Select
                      onValueChange={field.onChange}
                      value={field.value != null ? field.value.toString() : ''}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Servicio" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="max-h-64">
                        {services.map((service) => (
                          <SelectItem
                            key={service.id}
                            value={service.id.toString()}
                          >
                            {service.name}
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
                name="price"
                render={({ field }) => (
                  <FormItem className="w-full">
                    <Select
                      onValueChange={field.onChange}
                      value={field.value != null ? field.value.toString() : ''}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Precio" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="max-h-64">
                        {PRICES.map((price) => (
                          <SelectItem key={price} value={price.toString()}>
                            ${price}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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

export default ServiceSearch
