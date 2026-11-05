'use client'

import WorkerCard from './WorkerCard'
import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { type Worker } from '@/features/employees/types/types'
import WeeklyCalendar from '../../appointments/components/WeeklyCalendar'
import { fetchWorkersBySiteAndService } from '@/features/employees/api/workerApi'

export default function SelectWorker({
  id,
  site,
}: {
  id: string
  site: string
}) {
  const [workers, setWorkers] = useState<Worker[]>([])
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: session } = useSession()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchWorkersBySiteAndService(site, id)
        setWorkers(data)
      } catch (error) {
        console.error('Error fetching data:', error)
        setError('Unable to load the workers.')
      }
    }
    if (site) {
      fetchData()
    }
  }, [site, id])

  const handleWorkerSelect = (worker: Worker) => {
    setSelectedWorker(worker)
  }

  const handleAppointmentScheduled = () => {
    // You can add any logic here after an appointment is scheduled
    // For example, showing a success message or resetting the selection
    setSelectedWorker(null)
    alert('Appointment scheduled successfully!')
  }

  return (
    <main className="flex flex-col gap-20 px-10 my-10">
      <section className="flex flex-col gap-10 w-full max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold">Selecciona un profesional</h1>
        {error && <p className="text-red-500">{error}</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workers.map((worker) => (
            <WorkerCard
              key={worker.id}
              worker={worker}
              onSelect={handleWorkerSelect}
            />
          ))}
        </div>
        {selectedWorker && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">
              Agenda una cita con {selectedWorker.name}
            </h2>
            {session?.user?.id && (
              <WeeklyCalendar
                workerId={selectedWorker.id}
                siteId={Number.parseInt(site)}
                serviceId={Number.parseInt(id)}
                clientId={session.user.id}
                onAppointmentScheduled={handleAppointmentScheduled}
              />
            )}
          </div>
        )}
      </section>
    </main>
  )
}
