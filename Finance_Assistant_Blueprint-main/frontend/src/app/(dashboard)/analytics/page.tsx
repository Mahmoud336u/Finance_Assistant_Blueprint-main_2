"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { formatCurrency } from "@/lib/utils";
import { mockDashboard } from "@/lib/mock-data";
import { staggerContainerMedium as container, fadeInUp as item } from "@/lib/animations";

const tooltipStyle = {
  background: "hsl(224 25% 9%)",
  border: "1px solid hsl(224 15% 16%)",
  borderRadius: "8px",
  fontSize: "12px",
  color: "hsl(0 0% 95%)",
};

export default function AnalyticsPage() {
  const { spending_by_category, monthly_trend } = mockDashboard;

  const savingsData = monthly_trend.map((m) => ({
    month: m.month,
    savings: m.savings,
    rate: Math.round((m.savings / m.income) * 100),
  }));

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-sm text-foreground-muted">
            Insights into your financial patterns
          </p>
        </div>
        <span className="rounded-lg border border-warning/20 bg-warning-muted px-3 py-1 text-xs font-medium text-warning">
          Mock Data
        </span>
      </motion.div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Spending by Category Bar Chart */}
        <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-sm font-medium">Spending by Category</h2>
          <p className="mb-4 text-xs text-foreground-muted">This month breakdown</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={spending_by_category} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(224 15% 14%)" horizontal={false} />
              <XAxis type="number" stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v: number) => `$${v}`} />
              <YAxis type="category" dataKey="category_name" stroke="hsl(0 0% 45%)" fontSize={11} tickLine={false} axisLine={false} width={100} />
              <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [formatCurrency(value), "Spent"]} />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {spending_by_category.map((entry, i) => (
                  <Cell key={i} fill={entry.category_color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Category Distribution Pie */}
        <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-sm font-medium">Category Distribution</h2>
          <p className="mb-4 text-xs text-foreground-muted">Percentage of total spending</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={spending_by_category}
                dataKey="amount"
                nameKey="category_name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                strokeWidth={0}
              >
                {spending_by_category.map((entry, i) => (
                  <Cell key={i} fill={entry.category_color} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [formatCurrency(value), ""]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {spending_by_category.map((cat) => (
              <div key={cat.category_slug} className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: cat.category_color }} />
                <span className="truncate text-foreground-muted">{cat.category_name}</span>
                <span className="ml-auto font-medium tabular-nums">{cat.percentage}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Savings Trend */}
        <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-sm font-medium">Monthly Savings</h2>
          <p className="mb-4 text-xs text-foreground-muted">How much you&apos;re saving each month</p>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={savingsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(224 15% 14%)" />
              <XAxis dataKey="month" stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [formatCurrency(value), "Saved"]} />
              <Bar dataKey="savings" fill="hsl(160 84% 39%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Savings Rate Trend */}
        <motion.div variants={item} className="rounded-xl border border-border bg-card p-5">
          <h2 className="mb-1 text-sm font-medium">Savings Rate Trend</h2>
          <p className="mb-4 text-xs text-foreground-muted">Percentage of income saved</p>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={savingsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(224 15% 14%)" />
              <XAxis dataKey="month" stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(0 0% 45%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v: number) => `${v}%`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${value}%`, "Rate"]} />
              <Line type="monotone" dataKey="rate" stroke="hsl(210 100% 60%)" strokeWidth={2} dot={{ r: 4, fill: "hsl(210 100% 60%)" }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </motion.div>
  );
}
