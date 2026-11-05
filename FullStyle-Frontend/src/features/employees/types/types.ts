export interface Worker {
  id: number
  name: string
  site_id: number
  profilepicture: string
  description: string
  active: boolean
}

export interface Service {
  service_id: number
  service_name: string
}

export interface AddWorkerDialogProps {
  siteId: number
  services: Service[]
  onWorkerAdded: () => void
  open: boolean
  setOpen: (open: boolean) => void
}

export interface DeleteWorkerProps {
  showButton?: boolean
  setShowButton?: (open: boolean) => void
}

export interface WorkerCardProps {
  worker: Worker
  onSelect: (worker: Worker) => void
}

export interface Site {
  id: number
  name: string
  address: string
  phone: string
}
