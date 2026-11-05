'use client'

import { plans } from './data'
import Link from 'next/link'
import React, { useState } from 'react'
import { type Plan } from '@/features/plans/types/types'
import CardPlans from '@/features/plans/components/CardPlans'
import CheckoutDialog from '@/features/plans/components/CheckoutDialog'

export default function SubscriptionPlans() {
  // State to manage the selected plan and dialog visibility
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleSelectPlan = (plan: Plan) => {
    setSelectedPlan(plan)
    setIsDialogOpen(true)
  }

  return (
    <div className="container mx-auto py-10">
      <p className="text-center mb-4">
        El cobro comercial permanece deshabilitado.{' '}
        <Link className="underline" href="/operations">
          Usar suscripción sintética local
        </Link>
      </p>
      <h2 className="text-3xl font-bold text-center mb-8">
        Planes de Suscripción
      </h2>
      <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {plans.map((plan, index) => (
          <CardPlans key={plan.id} {...plan} onSelectPlan={handleSelectPlan} />
        ))}
      </div>
      <CheckoutDialog
        plan={selectedPlan}
        isOpen={isDialogOpen}
        onClose={() => {
          setIsDialogOpen(false)
        }}
      />
    </div>
  )
}
