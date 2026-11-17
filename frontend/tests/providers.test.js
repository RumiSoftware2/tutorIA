import test from 'node:test'
import assert from 'node:assert/strict'
import { buildChatPayload, canSelectProvider, PROVIDER_ORDER } from '../src/services/providers.js'

test('provider options preserve the requested order', () => {
  assert.deepEqual(PROVIDER_ORDER, ['openai', 'anthropic', 'groq', 'gemini'])
})

test('providers without configuration cannot be selected', () => {
  assert.equal(canSelectProvider({ status: 'requires_configuration' }), false)
  assert.equal(canSelectProvider({ status: 'temporarily_unavailable' }), true)
  assert.equal(canSelectProvider({ status: 'available' }), true)
})

test('chat payload includes the selected provider and conversation context', () => {
  const payload = buildChatPayload({ courseId: 'course-1', message: 'Factoriza', provider: 'groq', history: [] })
  assert.deepEqual(payload, { course_id: 'course-1', message: 'Factoriza', provider: 'groq', history: [] })
  assert.throws(() => buildChatPayload({ courseId: 'course-1', message: 'x', provider: 'invalid', history: [] }))
})
