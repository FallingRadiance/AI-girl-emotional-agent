import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000
})

export async function sendMessage(sessionId, message) {
  const { data } = await api.post('/chat', { session_id: sessionId, message })
  return data
}

export async function fetchMemory(sessionId) {
  const { data } = await api.get(`/memory/${sessionId}`)
  return data
}

export async function checkProactive(sessionId) {
  const { data } = await api.get(`/proactive/${sessionId}`)
  return data
}

export async function fetchTools() {
  const { data } = await api.get('/tools')
  return data.tools
}
