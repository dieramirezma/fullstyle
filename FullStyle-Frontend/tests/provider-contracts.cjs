const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')

function load(source, globals = {}) {
  const exports = {}
  const code = ts.transpileModule(fs.readFileSync(source, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText
  vm.runInNewContext(
    code,
    {
      exports,
      require: (name) => (name === '@/utils/apiClient' ? {} : require(name)),
      Buffer,
      console,
      ...globals,
    },
    { filename: source },
  )
  return exports
}

test('JWT cookies retain one token pair and compact legacy duplicated credentials', async () => {
  const { authOptions } = load('src/utils/sessionOptions.ts', {
    process: { env: {} },
  })
  const access =
    'header.' +
    Buffer.from(
      JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }),
    ).toString('base64url') +
    '.signature'
  const user = {
    id: 1,
    name: 'Synthetic',
    email: 'cookie@synthetic.invalid',
    token: access,
    refreshToken: 'private-refresh',
    active: true,
    is_manager: false,
  }
  const token = await authOptions.callbacks.jwt({ token: {}, user })
  assert.equal(token.accessToken, access)
  assert.equal(token.refreshToken, 'private-refresh')
  assert.equal('token' in token.user, false)
  assert.equal('refreshToken' in token.user, false)
  assert.equal(token.user.email, user.email)
  const legacy = await authOptions.callbacks.jwt({
    token: { ...token, user },
    user: undefined,
  })
  assert.equal('token' in legacy.user, false)
  assert.equal('refreshToken' in legacy.user, false)
})

test('operation boundaries reject malformed history and incomplete recovery codes', () => {
  const api = load('src/utils/operationContracts.ts')
  assert.equal(
    api.isChatHistory({
      turns: [
        {
          operation_id: 'one',
          state: 'uncertain',
          message: 'cancelar 1',
          reply: null,
        },
      ],
    }),
    true,
  )
  assert.equal(
    api.isChatHistory({
      turns: [
        { operation_id: 'one', state: 'uncertain', message: 'cancelar 1' },
      ],
    }),
    false,
  )
  assert.equal(
    api.isRecoveryCodes(
      Array.from({ length: 10 }, (_, index) =>
        index.toString(16).padStart(32, '0'),
      ),
    ),
    true,
  )
  assert.equal(api.isRecoveryCodes(Array(10).fill('a'.repeat(32))), false)
  assert.equal(api.isRecoveryCodes(['short']), false)
  assert.equal(
    api.isPaymentQuote({ appointment_id: 1, amount: 100, currency: 'COP' }),
    true,
  )
  assert.equal(
    api.isPaymentQuote({ appointment_id: 1, amount: -1, currency: 'COP' }),
    false,
  )
})

test('customer registration stays on the local GraphQL route with compatible fields', async () => {
  const calls = []
  const api = load('src/features/auth/api/authApi.ts', {
    fetch: async (...args) => {
      calls.push(args)
      return {
        ok: true,
        json: async () => ({
          data: { registerUser: { user: { id: 7 }, message: 'created' } },
        }),
      }
    },
  })
  const input = {
    name: 'Synthetic',
    email: 'synthetic@synthetic.invalid',
    password: 'synthetic-password',
  }
  const result = await api.registerCustomer(input)
  assert.equal(result.user.id, 7)
  assert.equal(calls[0][0], '/graphql')
  assert.deepEqual(JSON.parse(calls[0][1].body).variables, input)
})

test('registration reports upstream failure instead of accepting an empty response', async () => {
  const api = load('src/features/auth/api/authApi.ts', {
    fetch: async () => ({
      ok: false,
      json: async () => ({ errors: [{ message: 'Account rejected' }] }),
    }),
  })
  await assert.rejects(
    api.registerCustomer({ name: 'Synthetic' }),
    /Account rejected/,
  )
})

test('provider event verification rejects changes to signed values and malformed property paths', () => {
  const { verifyEvent } = load('src/utils/wompiEvent.ts')
  const body = {
    data: {
      transaction: {
        id: 'synthetic-1',
        status: 'APPROVED',
        amount_in_cents: 1000,
      },
    },
    timestamp: 1700000000,
    signature: {
      properties: [
        'transaction.id',
        'transaction.status',
        'transaction.amount_in_cents',
      ],
    },
  }
  const checksum = require('node:crypto')
    .createHash('sha256')
    .update('synthetic-1APPROVED10001700000000synthetic-secret')
    .digest('hex')
  assert.equal(
    verifyEvent(body, checksum.toUpperCase(), 'synthetic-secret'),
    true,
  )
  const changed = JSON.parse(JSON.stringify(body))
  changed.data.transaction.amount_in_cents = 1
  assert.equal(verifyEvent(changed, checksum, 'synthetic-secret'), false)
  changed.signature.properties = ['transaction.missing']
  assert.equal(verifyEvent(changed, checksum, 'synthetic-secret'), false)
  changed.signature.properties = ['__proto__.polluted']
  assert.equal(verifyEvent(changed, checksum, 'synthetic-secret'), false)
  assert.equal(verifyEvent(body, 'not-a-checksum', 'synthetic-secret'), false)
})
