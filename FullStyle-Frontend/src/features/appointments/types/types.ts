// Keep all the interfaces as they were...
export interface Service {
  id: number
  category_id: number
  name: string
}

export interface Category {
  id: number
  name: string
}

export interface Site {
  id: number
  name: string
  address: string
  phone: string
  manager_id: number
}

export interface WeeklyCalendarProps {
  workerId: number
  siteId: number
  serviceId: number
  clientId: number
  onAppointmentScheduled: () => void
}

export interface Worker {
  id: number
  name: string
  site_id: number
  profilepicture: string
  description: string
  active: boolean
}

export interface TimeSlot {
  start: string
  end: string
}

export interface DaySchedule {
  available: TimeSlot[]
  occupied: TimeSlot[]
}

export interface WeeklySchedule {
  worker_id: number
  week_start: string
  week_end: string
  schedule: Record<string, DaySchedule>
}

export interface AppointmentData {
  appointmenttime: string
  status: string
  worker_id: number
  site_id: number
  service_id: number
  client_id: number
  request: boolean
}

export interface AppointmentConfirmationDialogProps {
  isOpen: boolean
  onClose: () => void
  selectedSlot: string
  serviceDetail: Detail
  workerName: string
  siteDetail: Site
  appointmentData: AppointmentData | null
  onConfirm: () => Promise<void>
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
  description: string
  photos: Record<string, string>
}

export interface ErrorMessage {
  message: string
}

export interface ApiAppointment {
  id: number
  appointmenttime: string
  status: string
  client_id: number
  worker: {
    id: number
    name: string
    site_id: number
    profilepicture: string | null
    description: string
    active: boolean
  }
  site: {
    id: number
    name: string
    address: string
    phone: string
    manager_id: number
    photos: string | null
  }
  service: {
    service_id: number
    name: string
    site_id: number
    description: string
    price: number
    duration: number
    photos: string | null
    active: boolean
  }
}
