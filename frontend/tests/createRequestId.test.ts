import assert from 'node:assert/strict'
import test from 'node:test'
import { createRequestId } from '../src/utils/createRequestId.ts'

test('uses crypto.randomUUID when it is available', () => {
  const originalCrypto = Object.getOwnPropertyDescriptor(globalThis, 'crypto')
  Object.defineProperty(globalThis, 'crypto', {
    configurable: true,
    value: { randomUUID: () => 'secure-request-id' },
  })

  try {
    assert.equal(createRequestId(), 'secure-request-id')
  } finally {
    if (originalCrypto) Object.defineProperty(globalThis, 'crypto', originalCrypto)
  }
})

test('creates a fallback id when crypto.randomUUID is unavailable', () => {
  const originalCrypto = Object.getOwnPropertyDescriptor(globalThis, 'crypto')
  Object.defineProperty(globalThis, 'crypto', {
    configurable: true,
    value: {},
  })

  try {
    const requestId = createRequestId()
    assert.match(requestId, /^[a-z0-9]+-[a-z0-9]+$/)
    assert.ok(requestId.length > 3)
  } finally {
    if (originalCrypto) Object.defineProperty(globalThis, 'crypto', originalCrypto)
  }
})
