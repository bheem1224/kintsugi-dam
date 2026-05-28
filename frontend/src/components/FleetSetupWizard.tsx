import React, { useState } from 'react';

export function FleetSetupWizard({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(1);
  const [nodeType, setNodeType] = useState('ingestion');
  const [token, setToken] = useState('');

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else onComplete();
  };

  return (
    <div className="bg-black/40 backdrop-blur-md border border-white/10 rounded-xl p-8 max-w-2xl mx-auto shadow-2xl mt-10">
      <h2 className="text-2xl font-semibold text-white mb-6">Fleet Node Setup Wizard</h2>

      {step === 1 && (
        <div className="space-y-4 animate-in fade-in">
          <h3 className="text-lg text-white">Step 1: Select Node Type</h3>
          <p className="text-sm text-zinc-400">Choose the role for this new node based on your entitlement.</p>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <button
              onClick={() => setNodeType('ingestion')}
              className={`p-4 rounded-xl border text-left flex flex-col gap-2 transition-colors ${nodeType === 'ingestion' ? 'bg-blue-500/20 border-blue-500/50' : 'bg-zinc-900 border-white/10 hover:bg-zinc-800'}`}
            >
              <span className="font-medium text-white">Ingestion Gateway</span>
              <span className="text-xs text-zinc-400">Pro & Studio. Handles inbound file chunks and buffering.</span>
            </button>
            <button
              onClick={() => setNodeType('worker')}
              className={`p-4 rounded-xl border text-left flex flex-col gap-2 transition-colors ${nodeType === 'worker' ? 'bg-blue-500/20 border-blue-500/50' : 'bg-zinc-900 border-white/10 hover:bg-zinc-800'}`}
            >
              <span className="font-medium text-white">Compute Worker</span>
              <span className="text-xs text-zinc-400">Studio Only. Heavy compute coordination via Redis.</span>
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4 animate-in fade-in">
          <h3 className="text-lg text-white">Step 2: Connect to Control Plane</h3>
          <p className="text-sm text-zinc-400">Enter the registration token provided by your Kintsugi-DAM administrator to enroll this {nodeType} node.</p>
          <input
            type="text"
            placeholder="eyJh..."
            value={token}
            onChange={e => setToken(e.target.value)}
            className="w-full bg-zinc-950 border border-white/10 rounded-xl p-3 text-white font-mono mt-4"
          />
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4 animate-in fade-in">
          <h3 className="text-lg text-white">Step 3: Configuration Review</h3>
          <div className="bg-zinc-950 border border-white/10 rounded-xl p-4 text-sm text-zinc-300">
            <p><strong>Node Type:</strong> {nodeType === 'ingestion' ? 'Ingestion Gateway' : 'Compute Worker'}</p>
            <p><strong>Auth Protocol:</strong> mTLS Certificate Rotation</p>
            <p><strong>Status:</strong> Ready to Provision</p>
          </div>
          {nodeType === 'worker' && (
            <p className="text-xs text-yellow-500 mt-2">Note: Compute Worker requires Redis configuration in Fleet Settings after provisioning.</p>
          )}
        </div>
      )}

      <div className="flex justify-between mt-8 border-t border-white/10 pt-4">
        <button
          disabled={step === 1}
          onClick={() => setStep(step - 1)}
          className="px-4 py-2 text-zinc-400 hover:text-white disabled:opacity-50"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium"
        >
          {step === 3 ? 'Enroll Node' : 'Next'}
        </button>
      </div>
    </div>
  );
}
