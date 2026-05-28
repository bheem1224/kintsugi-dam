import React, { useState, useEffect } from 'react';

interface DirectoryPickerProps {
  value: string;
  onChange: (path: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function DirectoryPicker({ value, onChange, isOpen, onClose }: DirectoryPickerProps) {
  const [currentPath, setCurrentPath] = useState(value || '/');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadPath(currentPath);
    }
  }, [isOpen, currentPath]);

  const loadPath = async (path: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/fs/explore?path=${encodeURIComponent(path)}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items);
        setCurrentPath(data.current_path);
      }
    } catch (e) {
      console.error("Failed to load path", e);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden">
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-zinc-800/50">
          <h3 className="text-lg font-medium text-white">Select Directory</h3>
          <button onClick={onClose} className="text-zinc-400 hover:text-white">&times;</button>
        </div>

        <div className="p-3 border-b border-white/10 flex gap-2 items-center bg-zinc-900">
          <button
            disabled={currentPath === '/'}
            onClick={() => {
              const parts = currentPath.split('/').filter(Boolean);
              parts.pop();
              loadPath('/' + parts.join('/'));
            }}
            className="p-1 rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          </button>
          <div className="flex-1 px-3 py-1.5 bg-zinc-950 border border-white/10 rounded text-sm font-mono text-zinc-300 overflow-x-auto whitespace-nowrap">
            {currentPath}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 min-h-[300px]">
          {loading ? (
            <div className="flex items-center justify-center h-full text-zinc-500">Loading...</div>
          ) : items.length === 0 ? (
            <div className="flex items-center justify-center h-full text-zinc-500">Empty directory</div>
          ) : (
            <ul className="space-y-1">
              {items.map(item => (
                <li key={item.path}>
                  <button
                    disabled={!item.is_dir}
                    onClick={() => item.is_dir && loadPath(item.path)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded text-left ${item.is_dir ? 'hover:bg-zinc-800 text-zinc-200 cursor-pointer' : 'opacity-50 text-zinc-500 cursor-default'}`}
                  >
                    {item.is_dir ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                    )}
                    <span className="truncate">{item.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="p-4 border-t border-white/10 flex justify-end gap-3 bg-zinc-800/50">
          <button onClick={onClose} className="px-4 py-2 rounded text-sm text-zinc-300 hover:text-white">Cancel</button>
          <button
            onClick={() => {
              onChange(currentPath);
              onClose();
            }}
            className="px-4 py-2 rounded text-sm bg-blue-600 hover:bg-blue-500 text-white font-medium"
          >
            Select Current Directory
          </button>
        </div>
      </div>
    </div>
  );
}
