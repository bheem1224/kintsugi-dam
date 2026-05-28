import React, { useState, useEffect } from 'react';

export function ProfileBuilder() {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [editingProfile, setEditingProfile] = useState<any | null>(null);

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    const res = await fetch('/api/profiles');
    if (res.ok) {
      const data = await res.json();
      setProfiles(data);
    }
  };

  const saveProfile = async (profile: any) => {
    const isNew = !profile.id;
    const url = isNew ? '/api/profiles' : `/api/profiles/${profile.id}`;
    const method = isNew ? 'POST' : 'PUT';

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile)
    });
    setEditingProfile(null);
    fetchProfiles();
  };

  const deleteProfile = async (id: number) => {
    await fetch(`/api/profiles/${id}`, { method: 'DELETE' });
    fetchProfiles();
  };

  const addStep = (profile: any) => {
    const updated = { ...profile };
    if (!updated.payload_json.steps) updated.payload_json.steps = [];
    updated.payload_json.steps.push({ type: 'Veto Only', config: {} });
    setEditingProfile(updated);
  };

  const removeStep = (profile: any, index: number) => {
    const updated = { ...profile };
    updated.payload_json.steps.splice(index, 1);
    setEditingProfile(updated);
  };

  const updateStepType = (profile: any, index: number, type: string) => {
    const updated = { ...profile };
    updated.payload_json.steps[index].type = type;
    setEditingProfile(updated);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-medium text-white">Remediation Profiles</h3>
        <button
          onClick={() => setEditingProfile({ name: 'New Profile', payload_json: { steps: [] } })}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium"
        >
          + Add Profile
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map(p => (
          <div key={p.id} className="bg-zinc-900 border border-white/10 rounded-xl p-4 flex flex-col gap-4">
            <h4 className="font-medium text-white text-lg">{p.name}</h4>
            <div className="text-sm text-zinc-400">
              {p.payload_json?.steps?.length || 0} steps configured
            </div>
            <div className="flex gap-2 mt-auto pt-4 border-t border-white/10">
              <button onClick={() => setEditingProfile(p)} className="text-sm text-blue-400 hover:text-blue-300">Edit</button>
              <button onClick={() => deleteProfile(p.id)} className="text-sm text-red-400 hover:text-red-300 ml-auto">Delete</button>
            </div>
          </div>
        ))}
      </div>

      {editingProfile && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="p-4 border-b border-white/10 flex justify-between items-center bg-zinc-800/50">
              <h3 className="text-lg font-medium text-white">{editingProfile.id ? 'Edit Profile' : 'New Profile'}</h3>
              <button onClick={() => setEditingProfile(null)} className="text-zinc-400 hover:text-white">&times;</button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">Profile Name</label>
                <input
                  type="text"
                  value={editingProfile.name}
                  onChange={e => setEditingProfile({...editingProfile, name: e.target.value})}
                  className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="block text-sm font-medium text-zinc-300">Pipeline Steps</label>
                  <button onClick={() => addStep(editingProfile)} className="text-sm text-blue-400 hover:text-blue-300">+ Add Step</button>
                </div>

                <div className="space-y-3">
                  {(editingProfile.payload_json.steps || []).map((step: any, idx: number) => (
                    <div key={idx} className="flex gap-3 items-center bg-zinc-950 border border-white/10 p-3 rounded">
                      <div className="text-zinc-500 font-mono text-xs">{idx + 1}</div>
                      <select
                        value={step.type}
                        onChange={e => updateStepType(editingProfile, idx, e.target.value)}
                        className="bg-zinc-900 border border-white/10 rounded p-1.5 text-sm text-white flex-1"
                      >
                        <option value="Veto Only">Veto Only</option>
                        <option value="Aggressive Auto-Fix">Aggressive Auto-Fix</option>
                        <option value="Quarantine">Quarantine</option>
                        <option value="AI Repair">AI Repair</option>
                      </select>
                      <button onClick={() => removeStep(editingProfile, idx)} className="text-red-400 hover:text-red-300 p-1">
                         <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                      </button>
                    </div>
                  ))}
                  {(!editingProfile.payload_json.steps || editingProfile.payload_json.steps.length === 0) && (
                    <div className="text-zinc-500 text-sm text-center p-4 border border-dashed border-white/10 rounded">
                      No steps defined. Add a step to build the remediation pipeline.
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-white/10 flex justify-end gap-3 bg-zinc-800/50">
              <button onClick={() => setEditingProfile(null)} className="px-4 py-2 rounded text-sm text-zinc-300 hover:text-white">Cancel</button>
              <button
                onClick={() => saveProfile(editingProfile)}
                className="px-4 py-2 rounded text-sm bg-blue-600 hover:bg-blue-500 text-white font-medium"
              >
                Save Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
