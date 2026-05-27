"use client"

import React, { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { usePathname, useRouter } from "next/navigation";
import { SystemProvider } from "@/context/SystemContext";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token && pathname !== "/login") {
      router.push("/login");
    }
  }, [loading, token, pathname, router]);

  if (loading) {
    return <div className="h-screen w-screen flex items-center justify-center">Loading...</div>;
  }

  // Only render children if authenticated or if on the login page
  if (!token && pathname !== "/login") {
    return null;
  }

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <SystemProvider>
      <div className="flex flex-col md:flex-row flex-1 overflow-hidden h-screen w-screen">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden relative pb-16 md:pb-0">
           {/* Header is only visible on mobile now */}
           <Header />
           <main className="flex-1 overflow-auto bg-background p-6">
             {children}
           </main>
        </div>
      </div>
    </SystemProvider>
  );
}
