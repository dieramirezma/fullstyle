export interface Site {
  id: number
  name: string
  address: string
  phone: string
  manager_id: number
  photos: string
}

export interface Detail {
  site_id: number
  site_name: string
  site_address: string
  category_id: number
  category_name: string
  service_id: number
  service_name: string
  price: number
  duration: number
  description: string | null
  photos?: Record<string, string>
}

export interface Service {
  service_id: number
  site_id: number
  service_name: string
  price: number
  duration: number
  photos?: Record<string, string>
  description?: string
}

export interface AddServiceDialogProps {
  siteId: number
  services: Array<{ id: number; category_id: number; name: string }>
  onServiceAdded: () => void
  open: boolean
  setOpen: (open: boolean) => void
}

export interface EditServiceFormProps {
  service: Service
  onSave: (updatedService: Service) => void
  onCancel: () => void
}

export interface ServiceListProps {
  services: Service[]
  onServiceClick: (serviceId: number) => void
  onServiceUpdate: (updatedService: Service) => void
}
