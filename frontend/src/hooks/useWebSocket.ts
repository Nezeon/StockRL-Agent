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
  const reconnectTimeoutRef = useRef<number>()

  const connect = useCallback(() => {
    const token = localStorage.getItem('auth_token')
    const wsUrl = `${url}?token=${token}`

    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      setIsConnected(true)
      options.onConnect?.()
    }

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      options.onMessage(data)
    }

    wsRef.current.onclose = () => {
      setIsConnected(false)
      options.onDisconnect?.()

      // Reconnect after 3 seconds if enabled
      if (options.reconnect !== false) {
        reconnectTimeoutRef.current = window.setTimeout(connect, 3000)
      }
    }
  }, [url, options])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
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
