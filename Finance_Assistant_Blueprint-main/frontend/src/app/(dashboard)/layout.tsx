"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuthStore } from "@/lib/store/auth-store";
import { useUIStore } from "@/lib/store/ui-store";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuthStore();
  const { sidebarCollapsed } = useUIStore();
  const router = useRouter();

  useEffect(() => {
    // In mock mode, auto-login
    if (!isAuthenticated && process.env.NEXT_PUBLIC_MOCK_AUTH === "true") {
      useAuthStore.getState().login("demo@meridian.finance", "demo");
    } else if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-foreground-muted">Loading Meridian...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <Topbar />
      <main
        className={cn(
          "min-h-[calc(100vh-4rem)] p-6",
          "transition-[margin-left] duration-250 ease-[var(--ease-out-expo)]",
        )}
        style={{
          marginLeft: sidebarCollapsed ? 64 : 280,
        }}
      >
        {children}
      </main>
    </div>
  );
}
