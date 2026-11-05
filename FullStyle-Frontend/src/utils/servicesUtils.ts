import { CATEGORIES } from '@/types/constants'
import { fetchAllServicesByCategories } from '@/features/services/api/servicesApi'

export const fetchServices = async () => {
  const categories = CATEGORIES.map((category) => category.id)
  try {
    const response = await fetchAllServicesByCategories(categories)
    return response
  } catch (error) {
    console.error('Error fetching services:', error)
    return { available: [], selected: [] }
  }
}
