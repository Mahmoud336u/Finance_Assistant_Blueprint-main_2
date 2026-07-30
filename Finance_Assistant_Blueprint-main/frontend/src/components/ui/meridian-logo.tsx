"use client";

/**
 * Meridian Logo Component
 *
 * Uses the official brand mark: a balanced beam with solid/open weights
 * on a pivot stand. Two variants per the brand guide:
 * - Full mark (≥32px): stand + beam + pivot + weights
 * - Small glyph (<32px): beam + pivot + weights only
 *
 * Hover animation: beam warms, weights shift, pivot pulses.
 * All motion respects prefers-reduced-motion via CSS.
 */

import { type ReactNode } from "react";

interface MeridianLogoProps {
  /** Pixel size of the logo mark */
  size?: number;
  /** Whether sidebar is collapsed (hides text) */
  collapsed?: boolean;
  /** Whether to show "Meridian" text next to the mark */
  showText?: boolean;
  /** Text size variant */
  textSize?: "sm" | "md" | "lg" | "xl";
  /** Additional CSS classes */
  className?: string;
}

const textSizeMap = {
  sm: "text-base",
  md: "text-lg",
  lg: "text-2xl",
  xl: "text-4xl",
};

/**
 * Full mark: stand + beam + pivot + solid weight + open weight.
 * Used at 32px and above per brand guide.
 */
function FullMark({ size }: { size: number }) {
  return (
    <svg
      className="meridian-mark"
      width={size}
      height={size}
      viewBox="0 0 96 96"
      fill="none"
      role="img"
      aria-label="Meridian: a balanced beam resting on a stand"
      tabIndex={0}
    >
      {/* Stand */}
      <path className="m-stand" stroke="#8F6D26" strokeWidth="4.5" strokeLinecap="round" d="M 48 70 L 48 42" />
      <path className="m-stand" stroke="#8F6D26" strokeWidth="4.5" strokeLinecap="round" d="M 34 70 L 62 70" />
      {/* Beam */}
      <path className="m-beam" stroke="#8F6D26" strokeWidth="5" strokeLinecap="round" d="M 16 48 L 80 36" />
      {/* Pivot */}
      <circle className="m-pivot" fill="#E8C97A" cx="48" cy="42" r="4.5" />
      {/* Solid weight (heavier, left) */}
      <circle className="m-weight-solid" fill="#C89B3C" cx="16" cy="48" r="11" />
      {/* Open weight (lighter, right) */}
      <circle className="m-weight-open" stroke="#C89B3C" strokeWidth="4" cx="80" cy="36" r="7" fill="none" />
    </svg>
  );
}

/**
 * Small glyph: beam + pivot + weights only (no stand).
 * Purpose-built for <32px contexts per brand guide.
 */
function SmallGlyph({ size }: { size: number }) {
  return (
    <svg
      className="meridian-mark"
      width={size}
      height={size}
      viewBox="0 0 96 96"
      fill="none"
      role="img"
      aria-label="Meridian glyph"
      tabIndex={0}
    >
      <path className="m-beam" stroke="#8F6D26" strokeWidth="7" strokeLinecap="round" d="M 20 58 L 76 34" />
      <circle className="m-pivot" fill="#E8C97A" cx="48" cy="46" r="6" />
      <circle className="m-weight-solid" fill="#C89B3C" cx="20" cy="58" r="14" />
      <circle className="m-weight-open" stroke="#C89B3C" strokeWidth="6" cx="76" cy="34" r="10" fill="none" />
    </svg>
  );
}

export function MeridianLogo({
  size = 32,
  collapsed = false,
  showText = true,
  textSize = "md",
  className = "",
}: MeridianLogoProps) {
  // Brand guide: full mark at ≥32px, small glyph below 32px
  const Mark = size >= 32 ? FullMark : SmallGlyph;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="shrink-0">
        <Mark size={size} />
      </div>

      {showText && !collapsed && (
        <span
          className={`font-semibold tracking-tight text-[var(--meridian-canvas,#FBF6EE)] ${textSizeMap[textSize]}`}
        >
          Meridian
        </span>
      )}
    </div>
  );
}

/**
 * Large centered logo for splash/login pages.
 * Uses the full mark at 80px with the wordmark text below.
 */
export function MeridianLogoLarge({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col items-center ${className}`}>
      <MeridianLogo size={80} showText={false} />
      <h1 className="mt-5 text-4xl font-bold tracking-tight text-[var(--meridian-canvas,#FBF6EE)]">
        Meridian
      </h1>
    </div>
  );
}

/**
 * Loading variant — adds gentle seesaw animation.
 */
export function MeridianLogoLoading({ size = 48 }: { size?: number }) {
  return (
    <div className="flex flex-col items-center gap-3">
      <svg
        className="meridian-mark meridian-mark--loading"
        width={size}
        height={size}
        viewBox="0 0 96 96"
        fill="none"
        role="img"
        aria-label="Loading..."
      >
        <path className="m-stand" stroke="#8F6D26" strokeWidth="4.5" strokeLinecap="round" d="M 48 70 L 48 42" />
        <path className="m-stand" stroke="#8F6D26" strokeWidth="4.5" strokeLinecap="round" d="M 34 70 L 62 70" />
        <path className="m-beam" stroke="#8F6D26" strokeWidth="5" strokeLinecap="round" d="M 16 48 L 80 36" />
        <circle className="m-pivot" fill="#E8C97A" cx="48" cy="42" r="4.5" />
        <circle className="m-weight-solid" fill="#C89B3C" cx="16" cy="48" r="11" />
        <circle className="m-weight-open" stroke="#C89B3C" strokeWidth="4" cx="80" cy="36" r="7" fill="none" />
      </svg>
      <p className="text-sm text-foreground-muted">Loading Meridian...</p>
    </div>
  );
}
