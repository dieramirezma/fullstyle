'use client'

import { useEffect, useState } from 'react'

export default function InstanceInfo() {
  const [instanceId, setInstanceId] = useState<string>('Cargando...')

  useEffect(() => {
    const getInstanceId = () => {
      try {
        console.log('=== Debugging INSTANCE_ID ===')

        const publicInstanceId = process.env.NEXT_PUBLIC_INSTANCE_ID
        if (publicInstanceId) {
          setInstanceId(publicInstanceId)
          return
        }

        // Método 2: Intentar obtener desde window.__NEXT_DATA__
        const nextData = (
          window as Window & {
            __NEXT_DATA__?: { props?: { pageProps?: { instanceId?: unknown } } }
          }
        ).__NEXT_DATA__
        if (typeof nextData?.props?.pageProps?.instanceId === 'string') {
          setInstanceId(nextData.props.pageProps.instanceId)
          return
        }

        // Fallback final
        setInstanceId('Desconocida')
      } catch (error) {
        console.error('Error al obtener INSTANCE_ID:', error)
        setInstanceId('Error al cargar')
      }
    }

    getInstanceId()
  }, [])

  return (
    <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm z-50">
      <p>
        Instancia: <span className="font-bold">{instanceId}</span>
      </p>
    </div>
  )
}
