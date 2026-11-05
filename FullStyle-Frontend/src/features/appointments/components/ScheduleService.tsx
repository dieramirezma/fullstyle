'use client'

import Link from 'next/link'
import SiteCard from './SiteCard'
import { type Site } from '../types/types'
import { useState, useEffect } from 'react'
import {
  fetchSitesByService,
  fetchWorkersBySiteAndService,
} from '@/features/appointments/api/appointmentApi'

export default function ScheduleService({ id }: { id: string }) {
  const [sites, setSites] = useState<Site[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const allSites: Site[] = await fetchSitesByService(id)

        const filteredSites = await Promise.all(
          allSites.map(async (site) => {
            try {
              const workers = await fetchWorkersBySiteAndService(site.id, id)
              return workers.length > 0 ? site : null
            } catch (error) {
              return null
            }
          }),
        )

        setSites(filteredSites.filter((site): site is Site => Boolean(site)))
      } catch (e) {
        setError('No se pudieron cargar los sitios.')
      }
    }

    if (id) {
      fetchData()
    }
  }, [id])

  return (
    <main className="flex flex-col gap-20 px-10 my-10 md:px-28">
      <section className="flex flex-col gap-10 w-full max-w-4xl mx-auto">
        <div className="w-full mb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sites.map((site, index) => (
              <Link key={index} href={`/service/${id}/${site.id}`}>
                <SiteCard site={site} />
              </Link>
            ))}
          </div>
        </div>
        {error && (
          <div className="text-center text-red-500">
            <h2 className="font-bold">{error}</h2>
          </div>
        )}
      </section>
    </main>
  )
}
