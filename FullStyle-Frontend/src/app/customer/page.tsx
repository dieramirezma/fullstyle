import { SearchProvider } from '@/context/search-context'
import ServiceSearch from '@/features/appointments/components/ServiceSearch'
import { ServiceResults } from '@/features/appointments/components/ServiceResults'

export default function Page() {
  return (
    <SearchProvider>
      <main className="flex flex-col gap-20 px-4 sm:px-10 my-10">
        <section className="flex flex-col gap-10 w-full max-w-4xl mx-auto">
          <h1 className="title text-center">¿Qué deseas buscar hoy?</h1>
          <div className="w-full mb-4">
            <ServiceSearch />
          </div>
          <ServiceResults />
        </section>
      </main>
    </SearchProvider>
  )
}
