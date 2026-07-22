"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Download,
  ArrowUpDown,
  ChevronDown,
  Tag,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { mockTransactions } from "@/lib/mock-data";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.03 } },
};

const item = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
};

export default function TransactionsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<"date" | "amount">("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const filtered = mockTransactions
    .filter(
      (txn) =>
        !searchQuery ||
        txn.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        txn.merchant_name?.toLowerCase().includes(searchQuery.toLowerCase()),
    )
    .sort((a, b) => {
      if (sortField === "date") {
        return sortDir === "desc"
          ? new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
          : new Date(a.transaction_date).getTime() - new Date(b.transaction_date).getTime();
      }
      return sortDir === "desc" ? b.amount - a.amount : a.amount - b.amount;
    });

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Transactions</h1>
          <p className="text-sm text-foreground-muted">
            {mockTransactions.length} transactions this month
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-lg border border-warning/20 bg-warning-muted px-3 py-1 text-xs font-medium text-warning">
            Mock Data
          </span>
          <button className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground-muted hover:bg-surface-hover transition-colors">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div variants={item} className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-subtle" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-border bg-card py-2.5 pl-10 pr-4 text-sm placeholder:text-foreground-subtle focus:border-primary/40 focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors"
          />
        </div>
        <button className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2.5 text-sm text-foreground-muted hover:bg-surface-hover transition-colors">
          <Filter className="h-4 w-4" />
          Filters
          <ChevronDown className="h-3 w-3" />
        </button>
        <button
          onClick={() => {
            if (sortField === "date") {
              setSortDir(sortDir === "desc" ? "asc" : "desc");
            } else {
              setSortField("date");
              setSortDir("desc");
            }
          }}
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm transition-colors",
            sortField === "date"
              ? "border-primary/30 bg-primary/5 text-primary"
              : "border-border bg-card text-foreground-muted hover:bg-surface-hover",
          )}
        >
          <ArrowUpDown className="h-4 w-4" />
          Date {sortField === "date" && (sortDir === "desc" ? "↓" : "↑")}
        </button>
        <button
          onClick={() => {
            if (sortField === "amount") {
              setSortDir(sortDir === "desc" ? "asc" : "desc");
            } else {
              setSortField("amount");
              setSortDir("desc");
            }
          }}
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm transition-colors",
            sortField === "amount"
              ? "border-primary/30 bg-primary/5 text-primary"
              : "border-border bg-card text-foreground-muted hover:bg-surface-hover",
          )}
        >
          <ArrowUpDown className="h-4 w-4" />
          Amount {sortField === "amount" && (sortDir === "desc" ? "↓" : "↑")}
        </button>
      </motion.div>

      {/* Transaction Table */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-border px-5 py-3 text-xs font-medium text-foreground-muted">
          <span>Transaction</span>
          <span className="w-28 text-right">Category</span>
          <span className="w-24 text-right">Date</span>
          <span className="w-28 text-right">Amount</span>
        </div>

        {/* Rows */}
        {filtered.map((txn, i) => (
          <motion.div
            key={txn.id}
            variants={item}
            className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-4 border-b border-border/50 px-5 py-3.5 last:border-0 hover:bg-surface-hover transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-medium"
                style={{
                  backgroundColor: (txn.category_color || "#6b7280") + "18",
                  color: txn.category_color || "#6b7280",
                }}
              >
                {(txn.merchant_name || txn.description).charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">
                  {txn.merchant_name || txn.description}
                </p>
                <p className="truncate text-xs text-foreground-muted">
                  {txn.account_name}
                  {txn.is_recurring && (
                    <span className="ml-2 inline-flex items-center rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                      Recurring
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="w-28 text-right">
              <span
                className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
                style={{
                  backgroundColor: (txn.category_color || "#6b7280") + "15",
                  color: txn.category_color || "#6b7280",
                }}
              >
                <Tag className="h-3 w-3" />
                {txn.category_name}
              </span>
            </div>
            <span className="w-24 text-right text-xs text-foreground-muted tabular-nums">
              {new Date(txn.transaction_date).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })}
            </span>
            <span
              className={cn(
                "w-28 text-right text-sm font-semibold tabular-nums",
                txn.amount > 0 ? "text-success" : "text-foreground",
              )}
            >
              {txn.amount > 0 ? "+" : ""}
              {formatCurrency(txn.amount)}
            </span>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
}
