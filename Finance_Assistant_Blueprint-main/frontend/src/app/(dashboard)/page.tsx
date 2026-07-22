"use client";

import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PiggyBank,
  Heart,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { mockDashboard } from "@/lib/mock-data";
import { staggerContainer, fadeInUp, smoothEase } from "@/lib/animations";

export default function DashboardPage() {
  const data = mockDashboard;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={fadeInUp} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-foreground-muted">
            Your financial overview at a glance
          </p>
        </div>
        <span className="rounded-lg border border-warning/20 bg-warning-muted px-3 py-1 text-xs font-medium text-warning">
          Mock Data
        </span>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Net Worth"
          value={formatCurrency(data.net_worth, "USD", true)}
          change={data.net_worth_change}
          icon={<DollarSign className="h-4 w-4" />}
          accentColor="text-primary"
        />
        <KPICard
          title="Monthly Income"
          value={formatCurrency(data.total_income, "USD", true)}
          change={2.5}
          icon={<TrendingUp className="h-4 w-4" />}
          accentColor="text-success"
        />
        <KPICard
          title="Monthly Expenses"
          value={formatCurrency(data.total_expenses, "USD", true)}
          change={-4.1}
          icon={<TrendingDown className="h-4 w-4" />}
          accentColor="text-destructive"
        />
        <KPICard
          title="Savings Rate"
          value={`${data.savings_rate}%`}
          change={1.8}
          icon={<PiggyBank className="h-4 w-4" />}
          accentColor="text-primary"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Income vs Expenses Chart */}
        <motion.div
          variants={fadeInUp}
          className="col-span-1 rounded-xl border border-border bg-card p-5 lg:col-span-2"
        >
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-foreground">
                Income vs Expenses
              </h2>
              <p className="text-xs text-foreground-muted">Last 7 months</p>
            </div>
            <div className="flex gap-4 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-primary" />
                Income
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-destructive" />
                Expenses
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data.monthly_trend}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(160 84% 39%)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(160 84% 39%)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(0 84% 60%)" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="hsl(0 84% 60%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(224 15% 14%)" />
              <XAxis dataKey="month" stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{
                  background: "hsl(224 25% 9%)",
                  border: "1px solid hsl(224 15% 16%)",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "hsl(0 0% 95%)",
                }}
                formatter={(value: number) => [formatCurrency(value), ""]}
              />
              <Area type="monotone" dataKey="income" stroke="hsl(160 84% 39%)" strokeWidth={2} fill="url(#incomeGrad)" />
              <Area type="monotone" dataKey="expenses" stroke="hsl(0 84% 60%)" strokeWidth={2} fill="url(#expenseGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Spending Breakdown */}
        <motion.div
          variants={fadeInUp}
          className="rounded-xl border border-border bg-card p-5"
        >
          <h2 className="mb-1 text-sm font-medium text-foreground">
            Spending Breakdown
          </h2>
          <p className="mb-4 text-xs text-foreground-muted">This month</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={data.spending_by_category}
                dataKey="amount"
                nameKey="category_name"
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                strokeWidth={0}
              >
                {data.spending_by_category.map((entry, i) => (
                  <Cell key={i} fill={entry.category_color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "hsl(224 25% 9%)",
                  border: "1px solid hsl(224 15% 16%)",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "hsl(0 0% 95%)",
                }}
                formatter={(value: number) => [formatCurrency(value), ""]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-2">
            {data.spending_by_category.slice(0, 4).map((cat) => (
              <div key={cat.category_slug} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: cat.category_color }}
                  />
                  <span className="text-foreground-muted">{cat.category_name}</span>
                </span>
                <span className="font-medium">{formatCurrency(cat.amount)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Budget Progress + Health Score */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Budget Progress */}
        <motion.div
          variants={fadeInUp}
          className="col-span-1 space-y-3 rounded-xl border border-border bg-card p-5 lg:col-span-2"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-foreground">Budget Progress</h2>
            <span className="text-xs text-foreground-muted">July 2026</span>
          </div>
          {data.active_budgets.map((budget) => {
            const percent = budget.current_spent
              ? Math.min((budget.current_spent / budget.amount) * 100, 100)
              : 0;
            const isOver = percent >= 100;
            const isWarning = percent >= 80 && !isOver;

            return (
              <div key={budget.id} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: budget.category_color }}
                    />
                    {budget.name}
                  </span>
                  <span className="text-foreground-muted">
                    {formatCurrency(budget.current_spent || 0)} /{" "}
                    {formatCurrency(budget.amount)}
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
                    animate={{ width: `${percent}%` }}
                    transition={{ duration: 0.8, ease: smoothEase, delay: 0.3 }}
                  />
                </div>
              </div>
            );
          })}
        </motion.div>

        {/* Financial Health Score */}
        <motion.div
          variants={fadeInUp}
          className="flex flex-col items-center justify-center rounded-xl border border-border bg-card p-5"
        >
          <Heart className="mb-2 h-5 w-5 text-primary" />
          <p className="text-xs text-foreground-muted">Financial Health</p>
          <div className="relative mt-3 flex h-28 w-28 items-center justify-center">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50" cy="50" r="42"
                fill="none" stroke="hsl(224 15% 16%)" strokeWidth="8"
              />
              <motion.circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke="hsl(160 84% 39%)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 42}`}
                initial={{ strokeDashoffset: 2 * Math.PI * 42 }}
                animate={{
                  strokeDashoffset:
                    2 * Math.PI * 42 * (1 - data.financial_health_score / 100),
                }}
                transition={{ duration: 1.2, ease: smoothEase, delay: 0.5 }}
              />
            </svg>
            <span className="absolute text-3xl font-bold text-foreground">
              {data.financial_health_score}
            </span>
          </div>
          <p className="mt-2 text-xs font-medium text-primary">Excellent</p>
        </motion.div>
      </div>

      {/* Recent Transactions */}
      <motion.div
        variants={fadeInUp}
        className="rounded-xl border border-border bg-card p-5"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium text-foreground">
            Recent Transactions
          </h2>
          <a
            href="/transactions"
            className="text-xs text-primary hover:text-primary-hover transition-colors"
          >
            View all →
          </a>
        </div>
        <div className="space-y-1">
          {data.recent_transactions.map((txn) => (
            <div
              key={txn.id}
              className="flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors hover:bg-surface-hover"
            >
              <div className="flex items-center gap-3">
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium"
                  style={{
                    backgroundColor: (txn.category_color || "#6b7280") + "18",
                    color: txn.category_color || "#6b7280",
                  }}
                >
                  {(txn.merchant_name || txn.description).charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium">
                    {txn.merchant_name || txn.description}
                  </p>
                  <p className="text-xs text-foreground-muted">
                    {txn.category_name} · {txn.account_name}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p
                  className={cn(
                    "text-sm font-semibold tabular-nums",
                    txn.amount > 0 ? "text-success" : "text-foreground",
                  )}
                >
                  {txn.amount > 0 ? "+" : ""}
                  {formatCurrency(txn.amount)}
                </p>
                <p className="text-xs text-foreground-muted">
                  {new Date(txn.transaction_date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* AI Insights Card */}
      <motion.div
        variants={fadeInUp}
        className="gradient-border rounded-xl border border-primary/20 bg-card p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-medium text-foreground">AI Insights</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-lg bg-primary/5 p-3">
            <ArrowDownRight className="mt-0.5 h-4 w-4 shrink-0 text-success" />
            <p className="text-sm text-foreground-muted">
              Your <span className="text-foreground font-medium">Food & Dining</span> spending is{" "}
              <span className="text-success font-medium">12% lower</span> than last month. Great progress on your budget!
            </p>
          </div>
          <div className="flex items-start gap-3 rounded-lg bg-warning/5 p-3">
            <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <p className="text-sm text-foreground-muted">
              Your <span className="text-foreground font-medium">Shopping</span> budget is at{" "}
              <span className="text-warning font-medium">91%</span> with 9 days left. Consider slowing down to stay on track.
            </p>
          </div>
        </div>
        <a
          href="/chat"
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-hover transition-colors"
        >
          <Sparkles className="h-3 w-3" />
          Ask Meridian for more insights →
        </a>
      </motion.div>
    </motion.div>
  );
}

// ============================================================
// KPI Card Component
// ============================================================

function KPICard({
  title,
  value,
  change,
  icon,
  accentColor,
}: {
  title: string;
  value: string;
  change: number;
  icon: React.ReactNode;
  accentColor: string;
}) {
  const isPositive = change >= 0;

  return (
    <motion.div
      variants={fadeInUp}
      className="rounded-xl border border-border bg-card p-5 transition-colors hover:border-foreground-subtle/20"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground-muted">{title}</span>
        <span className={cn("rounded-lg bg-surface-hover p-1.5", accentColor)}>
          {icon}
        </span>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
      <div className="mt-1 flex items-center gap-1">
        {isPositive ? (
          <ArrowUpRight className="h-3 w-3 text-success" />
        ) : (
          <ArrowDownRight className="h-3 w-3 text-destructive" />
        )}
        <span
          className={cn(
            "text-xs font-medium",
            isPositive ? "text-success" : "text-destructive",
          )}
        >
          {formatPercent(change)}
        </span>
        <span className="text-xs text-foreground-subtle">vs last month</span>
      </div>
    </motion.div>
  );
}
