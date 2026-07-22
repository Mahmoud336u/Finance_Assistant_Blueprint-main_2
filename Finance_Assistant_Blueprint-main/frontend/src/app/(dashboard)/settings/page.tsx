"use client";

import { motion } from "framer-motion";
import { User, Shield, Bell, Palette, Globe, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth-store";
import { useUIStore } from "@/lib/store/ui-store";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
};

export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useUIStore();

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="max-w-2xl space-y-6">
      {/* Header */}
      <motion.div variants={item}>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-foreground-muted">Manage your account and preferences</p>
      </motion.div>

      {/* Profile */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <User className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-sm font-medium">Profile</h2>
        </div>
        <div className="space-y-4">
          <SettingRow label="Name" value={user?.full_name || "—"} />
          <SettingRow label="Email" value={user?.email || "—"} />
          <SettingRow label="Subscription" value={
            <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary capitalize">
              {user?.subscription_tier || "free"}
            </span>
          } />
          <SettingRow label="Member since" value={
            user?.created_at
              ? new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long" })
              : "—"
          } />
        </div>
      </motion.div>

      {/* Appearance */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Palette className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-sm font-medium">Appearance</h2>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setTheme("dark")}
            className={cn(
              "flex flex-1 flex-col items-center gap-2 rounded-xl border p-4 transition-all",
              theme === "dark"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-foreground-subtle/20",
            )}
          >
            <div className="h-16 w-full rounded-lg bg-[hsl(224_30%_6%)] border border-[hsl(224_15%_16%)]" />
            <span className="text-xs font-medium">Dark</span>
          </button>
          <button
            onClick={() => setTheme("light")}
            className={cn(
              "flex flex-1 flex-col items-center gap-2 rounded-xl border p-4 transition-all",
              theme === "light"
                ? "border-primary bg-primary/5"
                : "border-border hover:border-foreground-subtle/20",
            )}
          >
            <div className="h-16 w-full rounded-lg bg-white border border-gray-200" />
            <span className="text-xs font-medium">Light</span>
          </button>
        </div>
      </motion.div>

      {/* Security */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-sm font-medium">Security</h2>
        </div>
        <div className="space-y-4">
          <SettingRow label="Two-Factor Auth" value={
            <span className={cn(
              "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
              user?.mfa_enabled
                ? "bg-success-muted text-success"
                : "bg-muted text-foreground-muted",
            )}>
              {user?.mfa_enabled ? "Enabled" : "Disabled"}
            </span>
          } />
          <SettingRow label="Data Region" value={user?.data_region || "us-east-1"} />
        </div>
      </motion.div>

      {/* Notifications */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-4 w-4 text-foreground-muted" />
          <h2 className="text-sm font-medium">Notifications</h2>
        </div>
        <div className="space-y-4">
          <ToggleRow label="Budget alerts" description="Get notified when you approach budget limits" defaultChecked />
          <ToggleRow label="Large transactions" description="Alerts for transactions over $500" defaultChecked />
          <ToggleRow label="Weekly summary" description="Get a weekly spending summary email" />
          <ToggleRow label="AI insights" description="Receive AI-generated financial insights" defaultChecked />
        </div>
      </motion.div>

      {/* Danger zone */}
      <motion.div variants={item} className="rounded-xl border border-destructive/20 bg-card p-5">
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm font-medium text-destructive hover:text-destructive/80 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </motion.div>
    </motion.div>
  );
}

function SettingRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-foreground-muted">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  defaultChecked,
}: {
  label: string;
  description: string;
  defaultChecked?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-foreground-muted">{description}</p>
      </div>
      <label className="relative inline-flex cursor-pointer">
        <input type="checkbox" defaultChecked={defaultChecked} className="peer sr-only" />
        <div className="h-5 w-9 rounded-full bg-muted transition-colors peer-checked:bg-primary peer-focus-visible:ring-2 peer-focus-visible:ring-primary/20 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-foreground after:transition-transform peer-checked:after:translate-x-4" />
      </label>
    </div>
  );
}
