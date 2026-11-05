export interface ChatTurn {
  operation_id: string
  state: string
  message: string
  reply: string | null
}

export function isChatHistory(value: unknown): value is { turns: ChatTurn[] } {
  if (
    !value ||
    typeof value !== 'object' ||
    !('turns' in value) ||
    !Array.isArray(value.turns)
  )
    return false
  return value.turns.every(
    (turn: unknown) =>
      !!turn &&
      typeof turn === 'object' &&
      'operation_id' in turn &&
      typeof turn.operation_id === 'string' &&
      'state' in turn &&
      typeof turn.state === 'string' &&
      'message' in turn &&
      typeof turn.message === 'string' &&
      'reply' in turn &&
      (turn.reply === null || typeof turn.reply === 'string'),
  )
}

export function isRecoveryCodes(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length === 10 &&
    new Set(value).size === 10 &&
    value.every(
      (code: unknown) =>
        typeof code === 'string' && /^[a-f0-9]{32}$/.test(code),
    )
  )
}

export function isPaymentQuote(
  value: unknown,
): value is { appointment_id: number; amount: number; currency: string } {
  return (
    !!value &&
    typeof value === 'object' &&
    'appointment_id' in value &&
    typeof value.appointment_id === 'number' &&
    'amount' in value &&
    typeof value.amount === 'number' &&
    Number.isInteger(value.amount) &&
    value.amount > 0 &&
    'currency' in value &&
    value.currency === 'COP'
  )
}
