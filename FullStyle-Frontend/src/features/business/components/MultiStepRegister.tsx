'use client'

import { useState } from 'react'
import RegisterBusinessForm from './RegisterBusinessForm'
import RegisterCategoriesForm from './RegisterCategoriesForm'

export default function MultiStepRegistrationForm() {
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState<'business' | 'categories'>(
    'business',
  )

  const handleBusinessRegistered = (siteId: string) => {
    setBusinessId(siteId)
    setCurrentStep('categories')
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {currentStep === 'business' && (
        <RegisterBusinessForm
          className="w-full"
          urlCallback="/owner"
          onRegistrationComplete={handleBusinessRegistered}
        />
      )}

      {currentStep === 'categories' && businessId && (
        <RegisterCategoriesForm urlCallback={'/owner'} siteId={businessId} />
      )}
    </div>
  )
}
