const labels: Record<string, string> = {
  reference: 'Referencia',
  appointment_id: 'Reserva',
  amount: 'Importe (COP)',
  amount_in_cents: 'Importe (centavos)',
  currency: 'Moneda',
  state: 'Estado',
  status: 'Estado',
  expires_at: 'Vencimiento',
  synthetic: 'Prueba local',
  transaction_id: 'Transacción',
  payment_id: 'Pago',
  resolution: 'Resolución',
  transactions: 'Transacciones',
  subscriptions: 'Suscripciones',
  plans: 'Planes',
  plan: 'Plan',
  name: 'Nombre',
  days: 'Días',
  duplicate: 'Operación ya registrada',
  payment_applied: 'Pago aplicado',
  subscription_applied: 'Suscripción aplicada',
  reconciliation_required: 'Requiere conciliación',
  receipt_id: 'Recibo',
  event_id: 'Evento',
  events: 'Mensajes',
  attempts: 'Intentos',
  last_error: 'Último error',
  created_at: 'Fecha',
  appointmenttime: 'Horario',
  worker_id: 'Trabajador',
  client_id: 'Cliente',
  service_id: 'Servicio',
  site_id: 'Sede',
  id: 'Identificador',
  message: 'Mensaje',
  paymentmethod: 'Método',
  timestamp: 'Fecha',
}

export default function OperationResult({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span>—</span>
  if (Array.isArray(value))
    return value.length ? (
      <ul className="space-y-3">
        {value.map((item: unknown, index) => (
          <li className="border p-3" key={index}>
            <OperationResult value={item} />
          </li>
        ))}
      </ul>
    ) : (
      <p>No hay registros.</p>
    )
  if (typeof value === 'object')
    return (
      <dl className="space-y-2">
        {Object.entries(value).map(([key, item]) => (
          <div key={key} className="grid grid-cols-2 gap-3">
            <dt>{labels[key] ?? key.replaceAll('_', ' ')}</dt>
            <dd className="break-all">
              <OperationResult value={item} />
            </dd>
          </div>
        ))}
      </dl>
    )
  return (
    <span>
      {typeof value === 'boolean' ? (value ? 'Sí' : 'No') : String(value)}
    </span>
  )
}
