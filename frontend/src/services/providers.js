export const PROVIDER_ORDER = ['openai', 'anthropic', 'groq', 'gemini']

export function canSelectProvider(provider) {
  return provider?.status !== 'requires_configuration'
}

export function buildChatPayload({ courseId, message, provider, history }) {
  if (!PROVIDER_ORDER.includes(provider)) throw new Error('Selecciona un proveedor válido.')
  return { course_id: courseId, message, provider, history }
}
