const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function runScout(input, languagePreference = 'auto') {
  const response = await fetch(`${BASE_URL}/api/scout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input, language_preference: languagePreference }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const error = new Error(err?.detail?.message || 'Request failed')
    error.clarifyingQuestion = err?.detail?.clarifying_question || null
    error.status = response.status
    throw error
  }

  return response.json()
}

export async function fetchEvals() {
  const response = await fetch(`${BASE_URL}/api/evals/json`)
  if (!response.ok) return null
  return response.json()
}

export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/api/health`)
  if (!response.ok) return null
  return response.json()
}
