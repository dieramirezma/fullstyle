export interface Plan {
  id: number
  title: string
  price: string
  description: string
  features: string[]
  button: string
  popular: boolean
  icon: 'star' | 'sparkles' | 'crown'
}

export interface CardPlansProps extends Plan {
  onSelectPlan: (plan: Plan) => void
}
