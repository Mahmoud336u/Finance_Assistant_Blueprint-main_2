"use client";

import { Bell, Search, Moon, Sun } from "lucide-react";
import { useUIStore } from "@/lib/store/ui-store";
import { useAuthStore } from "@/lib/store/auth-store";
import { cn, getInitials } from "@/lib/utils";
import { mockNotifications } from "@/lib/mock-data";

export function Topbar() {
  const { theme, toggleTheme, sidebarCollapsed } = useUIStore();
  const { user } = useAuthStore();
  const unreadCount = mockNotifications.filter((n) => !n.is_read).length;

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-xl",
        "transition-[margin-left] duration-250 ease-[var(--ease-out-expo)]",
      )}
      style={{
        marginLeft: sidebarCollapsed ? 64 : 280,
      }}
    >
      {/* Search */}
      <button
        className={cn(
          "flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2",
          "text-sm text-foreground-muted transition-colors hover:border-foreground-subtle hover:text-foreground",
          "w-full max-w-sm",
        )}
        onClick={() => useUIStore.getState().setCommandMenuOpen(true)}
      >
        <Search className="h-4 w-4" />
        <span>Search anything...</span>
        <kbd className="ml-auto hidden rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-foreground-muted sm:inline">
          ⌘K
        </kbd>
      </button>

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-foreground-muted transition-colors hover:bg-surface-hover hover:text-foreground"
        >
          {theme === "dark" ? (
            <Sun className="h-[18px] w-[18px]" />
          ) : (
            <Moon className="h-[18px] w-[18px]" />
          )}
        </button>

        {/* Notifications */}
        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg text-foreground-muted transition-colors hover:bg-surface-hover hover:text-foreground">
          <Bell className="h-[18px] w-[18px]" />
          {unreadCount > 0 && (
            <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-white">
              {unreadCount}
            </span>
          )}
        </button>

        {/* User avatar */}
        <div className="ml-1 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
            {user?.full_name ? getInitials(user.full_name) : "U"}
          </div>
        </div>
      </div>
    </header>
  );
}
