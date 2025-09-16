import { useState, useEffect } from 'react'
import { getQuickJSExecutor } from '@/lib/services/quickjs-executor'

export const useFunctionNodeQuickJS = () => {
  const [isQuickJSReady, setQuickJSReady] = useState(false)
  const [initError, setInitError] = useState<string | undefined>()

  useEffect(() => {
    const initializeQuickJS = async () => {
      try {
        await getQuickJSExecutor()
        setQuickJSReady(true)
      } catch (error) {
        setInitError((error as Error).message)
        console.error('Failed to initialize QuickJS:', error)
      }
    }

    initializeQuickJS()
  }, [])

  return { isQuickJSReady, initError }
}
