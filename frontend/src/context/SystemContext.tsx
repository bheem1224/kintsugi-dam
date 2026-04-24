"use client"

import React, { createContext, useContext, useState, useEffect } from "react"
import { useAuth } from "./AuthContext"

type SystemStats = {
  total_files: number;
  corrupted_files: number;
  cloud_credits: number;
  current_scanner_state: string;
  total_quarantined: number;
  last_scan_time: string | null;
  watcher_active: boolean;
};

type SystemContextType = {
  stats: SystemStats | null;
  loading: boolean;
  refreshStats: () => Promise<void>;
};

const SystemContext = createContext<SystemContextType | undefined>(undefined);

export function SystemProvider({ children }: { children: React.ReactNode }) {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  const fetchStats = async () => {
    try {
      if (!token) return;
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/stats`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch system stats:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchStats();
      const interval = setInterval(fetchStats, 30000);
      return () => clearInterval(interval);
    }
  }, [token]);

  return (
    <SystemContext.Provider value={{ stats, loading, refreshStats: fetchStats }}>
      {children}
    </SystemContext.Provider>
  );
}

export function useSystem() {
  const context = useContext(SystemContext);
  if (context === undefined) {
    throw new Error("useSystem must be used within a SystemProvider");
  }
  return context;
}
