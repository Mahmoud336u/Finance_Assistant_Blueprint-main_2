"use client";

import { motion } from "framer-motion";
import {
  Landmark,
  RefreshCw,
  Plus,
  CheckCircle2,
  AlertCircle,
  CreditCard,
  Wallet,
  TrendingUp,
  Building,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { mockAccounts } from "@/lib/mock-data";
import { staggerContainerMedium as container, fadeInUp as item } from "@/lib/animations";

const accountIcons: Record<string, React.ElementType> = {
  checking: Wallet,
  savings: Building,
  credit: CreditCard,
  investment: TrendingUp,
  loan: Landmark,
  other: Landmark,
};

export default function AccountsPage() {
  const totalBalance = mockAccounts.reduce(
    (sum, acc) => sum + (acc.current_balance || 0),
    0,
  );

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Accounts</h1>
          <p className="text-sm text-foreground-muted">
            {mockAccounts.length} linked accounts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-lg border border-warning/20 bg-warning-muted px-3 py-1 text-xs font-medium text-warning">
            Mock Data
          </span>
          <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary-hover transition-colors">
            <Plus className="h-4 w-4" />
            Link Account
          </button>
        </div>
      </motion.div>

      {/* Total Balance */}
      <motion.div
        variants={item}
        className="rounded-xl border border-border bg-card p-6"
      >
        <p className="text-sm text-foreground-muted">Total Net Balance</p>
        <p className="mt-1 text-3xl font-semibold">{formatCurrency(totalBalance)}</p>
        <p className="mt-1 text-xs text-foreground-subtle">
          Across {mockAccounts.length} accounts
        </p>
      </motion.div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {mockAccounts.map((account) => {
          const IconComponent = accountIcons[account.account_type] || Landmark;
          const isNegative = (account.current_balance || 0) < 0;

          return (
            <motion.div
              key={account.id}
              variants={item}
              className="group rounded-xl border border-border bg-card p-5 transition-all hover:border-foreground-subtle/20"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-surface-hover">
                    <IconComponent className="h-5 w-5 text-foreground-muted" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">{account.account_name}</h3>
                    <p className="text-xs text-foreground-muted">
                      {account.institution_name}
                      {account.mask && ` · ••••${account.mask}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {account.sync_status === "active" ? (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-warning" />
                  )}
                  <span
                    className={cn(
                      "text-[10px] font-medium capitalize",
                      account.sync_status === "active"
                        ? "text-success"
                        : "text-warning",
                    )}
                  >
                    {account.sync_status}
                  </span>
                </div>
              </div>

              <div className="mt-5">
                <p className="text-xs text-foreground-muted">Current Balance</p>
                <p
                  className={cn(
                    "mt-0.5 text-2xl font-semibold tabular-nums",
                    isNegative ? "text-destructive" : "text-foreground",
                  )}
                >
                  {formatCurrency(account.current_balance || 0)}
                </p>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <span className="rounded-md bg-surface-hover px-2 py-1 text-[10px] font-medium text-foreground-muted capitalize">
                  {account.account_type}
                </span>
                <span className="rounded-md bg-surface-hover px-2 py-1 text-[10px] font-medium text-foreground-muted uppercase">
                  {account.currency_code}
                </span>
                <button className="ml-auto flex items-center gap-1 text-[10px] text-foreground-subtle opacity-0 group-hover:opacity-100 transition-opacity">
                  <RefreshCw className="h-3 w-3" />
                  Sync
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
