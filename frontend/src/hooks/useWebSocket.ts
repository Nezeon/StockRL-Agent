import { useEffect, useRef, useState, useCallback } from 'react'

interface UseWebSocketOptions {
  onMessage: (data: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnect?: boolean
}

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectTimeoutRef = useRef<number | undefined>(undefined)

  const connect = useCallback(() => {
    const token = localStorage.getItem('auth_token')
    const wsUrl = token ? `${url}?token=${token}` : url

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      options.onConnect?.()
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
        options.onMessage(data)
      } catch (err) {
        // don't crash on non-JSON payloads
        console.warn('Failed to parse websocket message', err)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      options.onDisconnect?.()

      // Reconnect after 3 seconds if enabled
      if (options.reconnect !== false) {
        reconnectTimeoutRef.current = window.setTimeout(connect, 3000)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error', err)
    }
  }, [url, options])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current !== undefined) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  const subscribe = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', channel }))
    }
  }, [])

  const unsubscribe = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe', channel }))
    }
  }, [])

  return { isConnected, subscribe, unsubscribe }
}
