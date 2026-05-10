import { useEffect, useRef, useState } from 'react'
import { wsUrl } from '../api/client'

interface WsMessage {
  type: 'progress' | 'status' | 'error'
  task_id: string
  progress?: number
  status?: string
  message?: string
}

export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(wsUrl())
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch {
        // ignore
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  return { connected }
}
