"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  MessageSquare,
  ArrowLeftRight,
  PiggyBank,
  Landmark,
  BarChart3,
  Settings,
  ChevronsLeft,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { smoothEase } from "@/lib/animations";
import { MeridianLogo } from "@/components/ui/meridian-logo";
import { useUIStore } from "@/lib/store/ui-store";

const navItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "AI Chat",
    href: "/chat",
    icon: MessageSquare,
    accent: true,
  },
  {
    label: "Transactions",
    href: "/transactions",
    icon: ArrowLeftRight,
  },
  {
    label: "Budgets",
    href: "/budgets",
    icon: PiggyBank,
  },
  {
    label: "Accounts",
    href: "/accounts",
    icon: Landmark,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
];

const bottomItems = [
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebarCollapse } = useUIStore();

  return (
    <motion.aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col",
        "border-r border-border bg-sidebar",
        "transition-[width] duration-250 ease-[var(--ease-out-expo)]",
      )}
      animate={{ width: sidebarCollapsed ? 64 : 280 }}
      transition={{ duration: 0.25, ease: smoothEase }}
    >
      {/* Logo */}
      <div className="logo-hover-target flex h-16 items-center border-b border-border px-3">
        <MeridianLogo
          size={sidebarCollapsed ? 28 : 32}
          collapsed={sidebarCollapsed}
          showText={!sidebarCollapsed}
        />
      </div>

      {/* New Chat button (for chat page) */}
      <div className="px-3 pt-4 pb-2">
        <Link
          href="/chat"
          className={cn(
            "flex items-center gap-2 rounded-lg px-3 py-2.5",
            "bg-primary/10 text-primary hover:bg-primary/15",
            "transition-colors duration-150",
            "border border-primary/20",
            sidebarCollapsed && "justify-center px-0",
          )}
        >
          <Plus className="h-4 w-4 shrink-0" />
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-sm font-medium"
              >
                New Chat
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5",
                "text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-sidebar-active text-sidebar-active-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-foreground",
                sidebarCollapsed && "justify-center px-0",
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-r-full bg-primary"
                  transition={{ type: "spring", stiffness: 350, damping: 30 }}
                />
              )}
              <item.icon
                className={cn(
                  "h-[18px] w-[18px] shrink-0",
                  isActive && "text-primary",
                )}
              />
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              {item.accent && !sidebarCollapsed && (
                <span className="ml-auto flex h-5 items-center rounded-full bg-primary/15 px-1.5 text-[10px] font-bold text-primary">
                  AI
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-border px-3 py-2">
        {bottomItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5",
                "text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-sidebar-active text-sidebar-active-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-hover hover:text-foreground",
                sidebarCollapsed && "justify-center px-0",
              )}
            >
              <item.icon className="h-[18px] w-[18px] shrink-0" />
              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          );
        })}

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebarCollapse}
          className={cn(
            "mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5",
            "text-sm text-foreground-subtle hover:bg-sidebar-hover hover:text-foreground",
            "transition-colors duration-150",
            sidebarCollapsed && "justify-center px-0",
          )}
        >
          <motion.div
            animate={{ rotate: sidebarCollapsed ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronsLeft className="h-[18px] w-[18px] shrink-0" />
          </motion.div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </motion.aside>
  );
}
