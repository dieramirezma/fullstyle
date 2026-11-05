export interface Site {
  id: number
  name: string
  address: string
  phone: string
  manager_id: number
  photos?: Record<string, string>
}

export interface ResponseGeo {
  location: {
    lat: number
    lng: number
  }
  formatted_address: string
}
