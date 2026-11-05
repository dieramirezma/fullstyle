import React from 'react'
import SelectWorker from '@/features/employees/components/SelectWorker'

export default async function Page({
  params,
}: {
  params: Promise<{ id: string; site: string }>
}) {
  const { id, site } = await params // Extraemos los valores

  return <SelectWorker id={id} site={site} />
}
