import { create } from 'zustand'

export type NotificationSeverity = 'info' | 'warning' | 'destructive'

export interface AppNotification {
  id: string
  event: string
  message: string
  severity: NotificationSeverity
  timestamp: Date
  read: boolean
}

interface NotificationStore {
  notifications: AppNotification[]
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearAll: () => void
  unreadCount: () => number
}

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  notifications: [],

  addNotification: (notification) => set((state) => ({
    notifications: [
      {
        ...notification,
        id: crypto.randomUUID(),
        timestamp: new Date(),
        read: false
      },
      ...state.notifications
    ].slice(0, 100) // keep last 100
  })),

  markAsRead: (id) => set((state) => ({
    notifications: state.notifications.map(n => n.id === id ? { ...n, read: true } : n)
  })),

  markAllAsRead: () => set((state) => ({
    notifications: state.notifications.map(n => ({ ...n, read: true }))
  })),

  clearAll: () => set({ notifications: [] }),

  unreadCount: () => get().notifications.filter(n => !n.read).length
}))
