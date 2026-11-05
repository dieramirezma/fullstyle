'use client'

import { useState } from 'react'
import { useSession } from 'next-auth/react'
import Link from 'next/link'
import OperationResult from '@/components/operation-result'
import { isPaymentQuote } from '@/utils/operationContracts'

export default function OperationsPage() {
  const { data: session } = useSession()
  const [reference, setReference] = useState('')
  const [appointment, setAppointment] = useState('')
  const [quote, setQuote] = useState<{
    appointment_id: number
    amount: number
    currency: string
  } | null>(null)
  const [site, setSite] = useState('')
  const [transaction, setTransaction] = useState('')
  const [eventId, setEventId] = useState('')
  const [reason, setReason] = useState('')
  const [output, setOutput] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function run(path: string, method = 'GET', body?: object) {
    setBusy(true)
    setError('')
    try {
      if (!session?.accessToken) throw new Error('Inicia sesión para continuar')
      const response = await fetch(`/api/logic/${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(10000),
      })
      const data = await response.json()
      if (!response.ok)
        throw new Error(String(data.message ?? 'Solicitud rechazada'))
      setOutput(data as unknown)
      return data as unknown
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operación no disponible')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="max-w-3xl mx-auto p-6 space-y-5">
      <h1 className="text-2xl font-bold">Reservas, pagos y correo locales</h1>
      <p>
        Las aprobaciones, suscripciones y reembolsos de esta página son
        simulaciones de prueba. No realizan cargos ni devuelven dinero real.
      </p>
      <Link className="underline" href="/chatbot">
        Volver al asistente
      </Link>
      <section className="space-y-2">
        <h2>Mis reservas</h2>
        <button
          disabled={busy}
          onClick={() => {
            void run('appointment')
          }}
        >
          Consultar reservas
        </button>
        <label className="block">
          Reserva para pagar{' '}
          <input
            className="border p-2"
            value={appointment}
            onChange={(event) => {
              setAppointment(event.target.value)
              setQuote(null)
            }}
          />
        </label>
        <button
          disabled={busy || !appointment}
          onClick={() => {
            void run(`payment/quote/${encodeURIComponent(appointment)}`).then(
              (data: unknown) => {
                if (isPaymentQuote(data)) setQuote(data)
              },
            )
          }}
        >
          Consultar precio de mi reserva
        </button>
        {quote && (
          <>
            <p>
              Precio confirmado: {quote.amount.toLocaleString('es-CO')}{' '}
              {quote.currency}
            </p>
            <button
              disabled={busy}
              onClick={() => {
                void run('payment', 'POST', {
                  appointment_id: quote.appointment_id,
                  amount: quote.amount,
                  paymentmethod: 'wompi',
                  status: 'pending',
                }).then((data: unknown) => {
                  if (
                    data &&
                    typeof data === 'object' &&
                    'reference' in data &&
                    typeof data.reference === 'string'
                  )
                    setReference(data.reference)
                })
              }}
            >
              Crear intención de pago local
            </button>
          </>
        )}
      </section>
      <section className="space-y-2">
        <h2>Intención de pago</h2>
        <label className="block">
          Referencia{' '}
          <input
            className="border p-2"
            value={reference}
            onChange={(event) => {
              setReference(event.target.value)
            }}
          />
        </label>
        <button
          disabled={busy || !reference}
          onClick={() => {
            void run(`payment/intents/${encodeURIComponent(reference)}`)
          }}
        >
          Consultar estado y vencimiento
        </button>{' '}
        <button
          disabled={busy || !reference}
          onClick={() => {
            void run(
              `payment/intents/${encodeURIComponent(reference)}`,
              'DELETE',
            )
          }}
        >
          Cancelar intención y reserva
        </button>{' '}
        <button
          disabled={busy || !reference}
          onClick={() => {
            void run('local/payments/simulate', 'POST', {
              reference,
              operation_id: crypto.randomUUID(),
            })
          }}
        >
          Simular aprobación local
        </button>
        <p>
          Una intención cancelada o vencida cierra la reserva. Para reservar
          otra vez, crea una reserva nueva. Las aprobaciones tardías pasan a
          conciliación.
        </p>
      </section>
      {session?.user?.is_manager && (
        <>
          <section className="space-y-2">
            <h2>Conciliación del negocio</h2>
            <label>
              Sede{' '}
              <input
                className="border p-2"
                value={site}
                onChange={(event) => {
                  setSite(event.target.value)
                }}
              />
            </label>{' '}
            <button
              disabled={busy || !site}
              onClick={() => {
                void run(
                  `payment/reconciliation?site_id=${encodeURIComponent(site)}`,
                )
              }}
            >
              Consultar transacciones
            </button>
            <label className="block">
              Transacción{' '}
              <input
                className="border p-2"
                value={transaction}
                onChange={(event) => {
                  setTransaction(event.target.value)
                }}
              />
            </label>
          </section>
          <section className="space-y-2">
            <h2>Suscripción sintética</h2>
            <button
              disabled={busy}
              onClick={() => {
                void run('subscriptions/catalog')
              }}
            >
              Consultar catálogo
            </button>{' '}
            <button
              disabled={busy}
              onClick={() => {
                void run('subscriptions', 'POST', { plan: 'synthetic-30-days' })
              }}
            >
              Crear intención de prueba de 30 días
            </button>{' '}
            <button
              disabled={busy}
              onClick={() => {
                void run('subscriptions')
              }}
            >
              Consultar mis suscripciones
            </button>
            <p>
              La intención solo se activa con una aprobación de prueba. Usa su
              referencia en el control anterior.
            </p>
          </section>
        </>
      )}
      <section className="space-y-2">
        <h2>Mis mensajes de correo</h2>
        <button
          disabled={busy}
          onClick={() => {
            void run('mail/events')
          }}
        >
          Consultar entregas y fallos
        </button>
        <label className="block">
          Identificador del evento{' '}
          <input
            className="border p-2"
            value={eventId}
            onChange={(event) => {
              setEventId(event.target.value)
            }}
          />
        </label>
        <p>
          Solo se reprograman mensajes de contacto válidos dirigidos a tu
          cuenta. Los mensajes entregados y los eventos inválidos se conservan
          sin repetirlos.
        </p>
      </section>
      <label className="block">
        Motivo de reembolso o reprogramación{' '}
        <textarea
          className="border p-2 w-full"
          value={reason}
          maxLength={500}
          onChange={(event) => {
            setReason(event.target.value)
          }}
        />
      </label>
      {session?.user?.is_manager && (
        <button
          disabled={busy || !transaction || !reason.trim()}
          onClick={() => {
            void run(
              `payment/refunds/${encodeURIComponent(transaction)}`,
              'POST',
              { reason, operation_id: crypto.randomUUID() },
            )
          }}
        >
          Registrar reembolso sintético y cancelar reserva
        </button>
      )}{' '}
      <button
        disabled={busy || !eventId || !reason.trim()}
        onClick={() => {
          void run(`mail/events/${encodeURIComponent(eventId)}/retry`, 'POST', {
            reason,
            operation_id: crypto.randomUUID(),
          })
        }}
      >
        Reprogramar correo local
      </button>
      {error && (
        <p role="alert" className="text-red-700">
          {error}
        </p>
      )}
      {output !== null && (
        <section aria-live="polite" className="border p-3">
          <OperationResult value={output} />
        </section>
      )}
    </main>
  )
}
