import React, { useState, useEffect } from 'react';

export function WorkerNodeConfig() {
  const [config, setConfig] = useState({
    redis_url: '',
    redis_port: '6379',
    redis_auth: '',
    path_mappings: '[]'
  });

  const [mappings, setMappings] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/fleet/worker-config')
      .then(r => r.json())
      .then(data => {
        setConfig(data);
        try {
          setMappings(JSON.parse(data.path_mappings || '[]'));
        } catch(e) {}
      })
      .catch(console.error);
  }, []);

  const saveConfig = async () => {
    await fetch('/api/fleet/worker-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, path_mappings: JSON.stringify(mappings) })
    });
    alert("Worker configuration saved.");
  };

  return (
    <div className="space-y-6 mt-6">
      <div className="p-4 border border-white/10 rounded-xl bg-black/20 space-y-4">
        <h4 className="text-lg font-medium text-white">Redis Compute Coordination</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Redis Host / URL</label>
            <input type="text" value={config.redis_url} onChange={e => setConfig({...config, redis_url: e.target.value})} className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white" />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1">Redis Port</label>
            <input type="text" value={config.redis_port} onChange={e => setConfig({...config, redis_port: e.target.value})} className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white" />
          </div>
        </div>
        <div>
            <label className="block text-sm text-zinc-400 mb-1">Redis Auth Password (Optional)</label>
            <input type="password" value={config.redis_auth} onChange={e => setConfig({...config, redis_auth: e.target.value})} className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white" />
        </div>
      </div>

      <div className="p-4 border border-white/10 rounded-xl bg-black/20 space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-lg font-medium text-white">Path Normalization</h4>
          <button onClick={() => setMappings([...mappings, { local_path: '', remote_path: '' }])} className="text-sm text-blue-400 hover:text-blue-300">+ Add Mapping</button>
        </div>
        <p className="text-xs text-zinc-400">Map Unraid local paths to Remote Worker mount paths so Redis jobs know where files reside.</p>

        {mappings.map((m, i) => (
          <div key={i} className="flex gap-2 items-center">
            <input
              type="text"
              placeholder="/mnt/user/media"
              value={m.local_path}
              onChange={e => { const nm = [...mappings]; nm[i].local_path = e.target.value; setMappings(nm); }}
              className="flex-1 bg-zinc-950 border border-white/10 rounded p-2 text-white text-sm"
            />
            <span className="text-zinc-500">→</span>
            <input
              type="text"
              placeholder="/remote_media"
              value={m.remote_path}
              onChange={e => { const nm = [...mappings]; nm[i].remote_path = e.target.value; setMappings(nm); }}
              className="flex-1 bg-zinc-950 border border-white/10 rounded p-2 text-white text-sm"
            />
            <button onClick={() => setMappings(mappings.filter((_, idx) => idx !== i))} className="text-red-400 hover:text-red-300 p-2">&times;</button>
          </div>
        ))}
      </div>

      <button onClick={saveConfig} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium">Save Worker Config</button>
    </div>
  );
}
