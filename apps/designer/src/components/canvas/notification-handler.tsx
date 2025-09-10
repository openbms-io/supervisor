'use client'

import { useEffect } from 'react'
import { toast } from 'sonner'
import { useFlowStore } from '@/store/use-flow-store'

export function NotificationHandler() {
  // Subscribe to notification changes
  const notification = useFlowStore((state) => state.notification)
  const clearNotification = useFlowStore((state) => state.clearNotification)

  useEffect(() => {
    if (!notification) return

    // Show toast based on notification type
    switch (notification.type) {
      case 'error':
        toast.error(notification.title, {
          description: notification.message,
          duration: 5000,
        })
        break

      case 'success':
        toast.success(notification.title, {
          description: notification.message,
          duration: 3000,
        })
        break

      case 'warning':
        toast.warning(notification.title, {
          description: notification.message,
          duration: 4000,
        })
        break

      default:
        toast(notification.title, {
          description: notification.message,
          duration: 3000,
        })
    }

    // Clear notification from store after showing
    // This prevents re-showing on re-renders
    clearNotification()
  }, [notification, clearNotification])

  // This component doesn't render anything visible
  return null
}
