"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Eye, EyeOff, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { smoothEase } from "@/lib/animations";
import { useAuthStore } from "@/lib/store/auth-store";

export default function LoginPage() {
  const [email, setEmail] = useState("demo@meridian.finance");
  const [password, setPassword] = useState("demo1234");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const { login, isLoading } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left Panel — Brand */}
      <div className="hidden w-1/2 flex-col items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-12 lg:flex">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: smoothEase }}
          className="max-w-md text-center"
        >
          <div className="mx-auto mb-8 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 glow-primary">
            <Sparkles className="h-10 w-10 text-primary" />
          </div>
          <h1 className="mb-3 text-4xl font-bold tracking-tight">
            <span className="text-gradient">Meridian</span>
          </h1>
          <p className="text-lg text-foreground-muted">
            AI-Powered Financial Intelligence
          </p>
          <p className="mt-4 text-sm text-foreground-subtle leading-relaxed">
            Track spending, manage budgets, and get intelligent insights
            from your personal AI financial advisor — all in one
            premium experience.
          </p>

          {/* Feature highlights */}
          <div className="mt-10 grid grid-cols-3 gap-6 text-center">
            {[
              { stat: "AI Chat", desc: "Financial advisor" },
              { stat: "Real-time", desc: "Transaction sync" },
              { stat: "Smart", desc: "Budget alerts" },
            ].map((f) => (
              <div key={f.stat}>
                <p className="text-sm font-semibold text-primary">{f.stat}</p>
                <p className="mt-0.5 text-xs text-foreground-subtle">{f.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="flex w-full flex-col items-center justify-center px-8 lg:w-1/2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: smoothEase }}
          className="w-full max-w-sm"
        >
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <span className="text-xl font-semibold">Meridian</span>
          </div>

          <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
          <p className="mt-1 text-sm text-foreground-muted">
            Sign in to your account to continue
          </p>

          {/* Dev mode notice */}
          <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs text-primary">
            <span className="font-semibold">Dev Mode:</span> Click sign in — credentials are pre-filled.
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-border bg-card px-3 py-2.5 text-sm focus:border-primary/40 focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground-muted">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2.5 pr-10 text-sm focus:border-primary/40 focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-subtle hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-xs text-destructive">{error}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                "flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 text-sm font-medium text-primary-foreground",
                "transition-all hover:bg-primary-hover",
                "disabled:cursor-not-allowed disabled:opacity-60",
              )}
            >
              {isLoading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <>
                  Sign In
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-foreground-subtle">
            Don&apos;t have an account?{" "}
            <a href="#" className="font-medium text-primary hover:text-primary-hover transition-colors">
              Sign up
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
