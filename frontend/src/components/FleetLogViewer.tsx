import React, { useState, useEffect, useRef } from 'react';

export function FleetLogViewer({ nodeId }: { nodeId: string }) {
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!nodeId) return;

    setLogs([`Connecting to log stream for node ${nodeId}...`]);

    // Server-Sent Events setup
    const evtSource = new EventSource(`/api/fleet/logs/${nodeId}`);

    evtSource.onmessage = (event) => {
      setLogs(prev => {
        const newLogs = [...prev, event.data];
        return newLogs.slice(-100); // Keep last 100 logs in UI memory
      });
    };

    evtSource.onerror = () => {
      setLogs(prev => [...prev, "Connection lost or node offline. Attempting to reconnect..."]);
    };

    return () => {
      evtSource.close();
    };
  }, [nodeId]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="bg-black border border-white/10 rounded-xl mt-6 font-mono text-xs overflow-hidden flex flex-col h-96">
      <div className="bg-zinc-900 border-b border-white/10 p-2 text-zinc-400 flex justify-between items-center">
        <span>Live Stream: {nodeId}</span>
        <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> Connected</span>
      </div>
      <div className="flex-1 p-4 overflow-y-auto space-y-1">
        {logs.map((log, i) => (
          <div key={i} className={`${log.includes('ERROR') ? 'text-red-400' : log.includes('WARN') ? 'text-yellow-400' : 'text-zinc-300'}`}>
            {log}
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
