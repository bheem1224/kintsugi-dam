import { useEffect, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useNotificationStore, NotificationSeverity } from '@/store/useNotificationStore';
import { toast } from 'sonner';

export function useNexusStream(token: string | null) {
  const addNotification = useNotificationStore(state => state.addNotification);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!token) return;

    controllerRef.current = new AbortController();

    const connect = async () => {
      await fetchEventSource('/api/events/stream', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'text/event-stream',
        },
        signal: controllerRef.current?.signal,
        async onmessage(ev) {
          try {
            let payload: Record<string, unknown> = { message: ev.data };
            try {
              payload = JSON.parse(ev.data);
            } catch (e) {
                // Ignore parse error, it's just raw text
            }

            const eventType = (ev.event || payload.event || 'unknown') as string;
            const message = (payload.message || payload.detail || ev.data) as string;

            let severity: NotificationSeverity = 'info';

            if (eventType === 'event:triage:quarantined') {
              severity = 'warning';
              toast.warning(`Quarantine: ${message}`);
            } else if (eventType === 'event:system:error' || eventType === 'event:fleet:banned') {
              severity = 'destructive';
              toast.error(`System Alert: ${message}`, { style: { backgroundColor: 'red', color: 'white' }});
            } else if (eventType.startsWith('event:remediator:')) {
              severity = 'info';
              // No toast for info
            } else {
               severity = 'info';
            }

            addNotification({
              event: eventType,
              message: message,
              severity: severity
            });

          } catch (err) {
            console.error('Error processing SSE message:', err);
          }
        },
        onclose() {
           // Will retry automatically
        },
        onerror(err) {
          console.error('SSE Error:', err);
          // throw err to trigger retry, or return to stop
        }
      });
    };

    connect();

    return () => {
      controllerRef.current?.abort();
    };
  }, [token, addNotification]);
}
