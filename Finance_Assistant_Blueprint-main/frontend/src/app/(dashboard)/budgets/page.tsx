"use client";

import { motion } from "framer-motion";
import { Plus, PiggyBank, TrendingDown, AlertTriangle } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { mockBudgets } from "@/lib/mock-data";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

export default function BudgetsPage() {
  const totalBudget = mockBudgets.reduce((sum, b) => sum + b.amount, 0);
  const totalSpent = mockBudgets.reduce((sum, b) => sum + (b.current_spent || 0), 0);
  const totalPercent = Math.round((totalSpent / totalBudget) * 100);

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Budgets</h1>
          <p className="text-sm text-foreground-muted">
            Track and manage your spending limits
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-lg border border-warning/20 bg-warning-muted px-3 py-1 text-xs font-medium text-warning">
            Mock Data
          </span>
          <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary-hover transition-colors">
            <Plus className="h-4 w-4" />
            New Budget
          </button>
        </div>
      </motion.div>

      {/* Overview Card */}
      <motion.div
        variants={item}
        className="rounded-xl border border-border bg-card p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm text-foreground-muted">Total Monthly Budget</p>
            <p className="text-3xl font-semibold mt-1">{formatCurrency(totalBudget)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-foreground-muted">Spent so far</p>
            <p className="text-3xl font-semibold mt-1 text-foreground-muted">
              {formatCurrency(totalSpent)}
            </p>
          </div>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            className={cn(
              "h-full rounded-full",
              totalPercent >= 100
                ? "bg-destructive"
                : totalPercent >= 80
                  ? "bg-warning"
                  : "bg-primary",
            )}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(totalPercent, 100)}%` }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
        <p className="mt-2 text-xs text-foreground-muted">
          {totalPercent}% of total budget used · {formatCurrency(totalBudget - totalSpent)} remaining
        </p>
      </motion.div>

      {/* Budget Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {mockBudgets.map((budget) => {
          const percent = budget.current_spent
            ? Math.round((budget.current_spent / budget.amount) * 100)
            : 0;
          const remaining = budget.amount - (budget.current_spent || 0);
          const isOver = percent >= 100;
          const isWarning = percent >= 80 && !isOver;

          return (
            <motion.div
              key={budget.id}
              variants={item}
              className={cn(
                "rounded-xl border bg-card p-5 transition-all hover:border-foreground-subtle/20",
                isOver
                  ? "border-destructive/30"
                  : isWarning
                    ? "border-warning/30"
                    : "border-border",
              )}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-lg"
                    style={{
                      backgroundColor: (budget.category_color || "#6b7280") + "18",
                      color: budget.category_color || "#6b7280",
                    }}
                  >
                    <PiggyBank className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">{budget.name}</h3>
                    <p className="text-xs text-foreground-muted capitalize">{budget.period}</p>
                  </div>
                </div>
                {isWarning && (
                  <AlertTriangle className="h-4 w-4 text-warning" />
                )}
                {isOver && (
                  <AlertTriangle className="h-4 w-4 text-destructive" />
                )}
              </div>

              <div className="flex items-end justify-between mb-2">
                <span className="text-2xl font-semibold">
                  {formatCurrency(budget.current_spent || 0)}
                </span>
                <span className="text-sm text-foreground-muted">
                  of {formatCurrency(budget.amount)}
                </span>
              </div>

              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  className={cn(
                    "h-full rounded-full",
                    isOver
                      ? "bg-destructive"
                      : isWarning
                        ? "bg-warning"
                        : "bg-primary",
                  )}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(percent, 100)}%` }}
                  transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
                />
              </div>

              <div className="mt-2 flex items-center justify-between text-xs">
                <span
                  className={cn(
                    "font-medium",
                    isOver
                      ? "text-destructive"
                      : isWarning
                        ? "text-warning"
                        : "text-foreground-muted",
                  )}
                >
                  {percent}% used
                </span>
                <span className={cn(
                  remaining < 0 ? "text-destructive" : "text-foreground-muted",
                )}>
                  {remaining < 0 ? "Over by " + formatCurrency(Math.abs(remaining)) : formatCurrency(remaining) + " left"}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
