'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { isChatHistory } from '@/utils/operationContracts'
import { useSession } from 'next-auth/react'

const CHATBOT_API_URL = '/chatbot/api/v1/chat/send'

export default function ChatbotPage() {
  const { data: session } = useSession()
  const [sessionId, setSessionId] = useState('')
  const [turns, setTurns] = useState<
    Array<{
      operation_id: string
      state: string
      message: string
      reply: string | null
    }>
  >([])
  const [checked, setChecked] = useState(false)
  const [note, setNote] = useState('')
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function history(id: string) {
    const result = await fetch(
      `/chatbot/api/v1/chat/history/${encodeURIComponent(id)}`,
      { headers: { Authorization: `Bearer ${session?.accessToken}` } },
    )
    if (!result.ok) throw new Error('Historial no disponible')
    const data: unknown = await result.json()
    if (!isChatHistory(data)) throw new Error('Respuesta de historial inválida')
    setTurns(data.turns)
  }

  async function review(operation: string) {
    setLoading(true)
    try {
      const result = await fetch(
        `/chatbot/api/v1/chat/history/${encodeURIComponent(sessionId)}/operations/${encodeURIComponent(operation)}/review`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session?.accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ note, checked_booking_state: checked }),
        },
      )
      if (!result.ok)
        throw new Error(
          'No se pudo registrar la revisión; la operación podría seguir en curso',
        )
      await history(sessionId)
      setChecked(false)
      setNote('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Revisión no disponible')
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResponse('')
    const id = sessionId || crypto.randomUUID()
    setSessionId(id)
    try {
      if (!session?.accessToken)
        throw new Error('Inicia sesión para usar el asistente')
      const res = await fetch(CHATBOT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.accessToken}`,
          'X-Operation-ID': crypto.randomUUID(),
        },
        body: JSON.stringify({ message, session_id: id }),
        signal: AbortSignal.timeout(15000),
      })
      if (!res.ok) throw new Error('Error sending message')
      const data = await res.json()
      setResponse(String(data.reply ?? JSON.stringify(data)))
    } catch (err: any) {
      setError(String(err.message) || 'Unknown error')
    } finally {
      try {
        await history(id)
      } catch {
        /* Preserve the send error for review. */
      }
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <h1 className="text-2xl font-bold mb-4">Chatbot</h1>
      <Link className="underline" href="/operations">
        Consultar reservas, pagos y correo
      </Link>
      <label>
        Conversación (guarda el identificador para continuar)
        <input
          className="border p-2"
          value={sessionId}
          onChange={(event) => {
            setSessionId(event.target.value)
          }}
          maxLength={120}
        />
      </label>
      <button
        disabled={loading || !sessionId}
        onClick={() => {
          void history(sessionId).catch(() => {
            setError('Historial no disponible')
          })
        }}
      >
        Cargar historial
      </button>
      <form
        onSubmit={handleSend}
        className="flex flex-col gap-2 w-full max-w-md"
      >
        <input
          type="text"
          className="border rounded px-3 py-2 focus:outline-none focus:ring"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => {
            setMessage(e.target.value)
          }}
          required
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
      {response && (
        <div className="mt-4 p-3 bg-green-100 rounded w-full max-w-md">
          <strong>Response:</strong> {response}
        </div>
      )}
      {error && (
        <div className="mt-4 p-3 bg-red-100 rounded w-full max-w-md text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}
      <p>
        El contenido terminado o revisado se elimina después de 30 días; se
        conservan identificadores para impedir repetir operaciones.
      </p>
      {turns.map((turn) => (
        <article className="border p-3 w-full max-w-md" key={turn.operation_id}>
          <p>{turn.message}</p>
          <p>{turn.reply}</p>
          <p>Estado: {turn.state}</p>
          {['pending', 'uncertain'].includes(turn.state) && (
            <>
              <p>
                Resultado incierto. Consulta tus reservas antes de repetir una
                acción. Esta revisión no ejecuta la operación ni confirma su
                resultado.
              </p>
              <label>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(event) => {
                    setChecked(event.target.checked)
                  }}
                />{' '}
                Ya consulté el estado de mi reserva
              </label>
              <input
                aria-label="Nota de revisión"
                className="border p-2"
                value={note}
                maxLength={500}
                onChange={(event) => {
                  setNote(event.target.value)
                }}
              />
              <button
                disabled={loading || !checked || !note.trim()}
                onClick={() => {
                  void review(turn.operation_id)
                }}
              >
                Registrar revisión
              </button>
            </>
          )}
        </article>
      ))}
    </div>
  )
}
