"use client";

import { motion } from "framer-motion";

interface MeridianLogoProps {
  size?: number;
  collapsed?: boolean;
  showText?: boolean;
  textSize?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

/**
 * Meridian Logo
 *
 * A premium, warm-toned logo featuring two overlapping arcs that form
 * a subtle "M" shape — evoking a compass meridian and a protective embrace.
 * Uses warm amber → coral → rose gradient for a caring, trustworthy feel.
 *
 * Hover: subtle scale + glow pulse
 */
export function MeridianLogo({
  size = 32,
  collapsed = false,
  showText = true,
  textSize = "md",
  className = "",
}: MeridianLogoProps) {
  const textSizes = {
    sm: "text-base",
    md: "text-lg",
    lg: "text-2xl",
    xl: "text-4xl",
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <motion.div
        className="relative shrink-0"
        whileHover={{
          scale: 1.08,
          rotate: [0, -3, 3, 0],
          transition: { duration: 0.5, ease: "easeInOut" },
        }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Glow layer (visible on hover via CSS) */}
        <div
          className="logo-glow absolute inset-0 rounded-xl opacity-0 blur-lg transition-opacity duration-500"
          style={{
            background:
              "radial-gradient(circle, rgba(251, 146, 60, 0.4) 0%, rgba(244, 114, 182, 0.2) 50%, transparent 70%)",
            width: size + 8,
            height: size + 8,
            top: -4,
            left: -4,
          }}
        />

        <svg
          width={size}
          height={size}
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10"
        >
          <defs>
            {/* Main warm gradient — amber to coral to rose */}
            <linearGradient
              id="logoGradientMain"
              x1="4"
              y1="4"
              x2="44"
              y2="44"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#F59E0B" />
              <stop offset="50%" stopColor="#FB923C" />
              <stop offset="100%" stopColor="#F472B6" />
            </linearGradient>

            {/* Inner accent gradient */}
            <linearGradient
              id="logoGradientInner"
              x1="12"
              y1="12"
              x2="36"
              y2="36"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#FBBF24" />
              <stop offset="100%" stopColor="#FB7185" />
            </linearGradient>

            {/* Soft shadow */}
            <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow
                dx="0"
                dy="1"
                stdDeviation="2"
                floodColor="#FB923C"
                floodOpacity="0.25"
              />
            </filter>
          </defs>

          {/* Background rounded square */}
          <rect
            x="2"
            y="2"
            width="44"
            height="44"
            rx="12"
            fill="url(#logoGradientMain)"
            opacity="0.12"
          />

          {/* Left arc — represents protection/embrace */}
          <motion.path
            d="M14 36 C14 20, 24 12, 24 12"
            stroke="url(#logoGradientMain)"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
            filter="url(#logoShadow)"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: "easeOut", delay: 0.1 }}
          />

          {/* Right arc — mirrors the left, completing the "M" shape */}
          <motion.path
            d="M24 12 C24 12, 34 20, 34 36"
            stroke="url(#logoGradientMain)"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
            filter="url(#logoShadow)"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
          />

          {/* Center down-stroke — the meridian line */}
          <motion.path
            d="M24 16 L24 34"
            stroke="url(#logoGradientInner)"
            strokeWidth="3"
            strokeLinecap="round"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.6 }}
          />

          {/* Top dot — compass point / north star */}
          <motion.circle
            cx="24"
            cy="10"
            r="2.5"
            fill="url(#logoGradientInner)"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, delay: 1 }}
          />

          {/* Subtle base line — grounding element */}
          <motion.line
            x1="16"
            y1="38"
            x2="32"
            y2="38"
            stroke="url(#logoGradientMain)"
            strokeWidth="2.5"
            strokeLinecap="round"
            opacity="0.6"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          />
        </svg>
      </motion.div>

      {/* Text */}
      {showText && !collapsed && (
        <motion.span
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -8 }}
          transition={{ duration: 0.2 }}
          className={`font-semibold tracking-tight text-foreground ${textSizes[textSize]}`}
        >
          Meridian
        </motion.span>
      )}
    </div>
  );
}

/**
 * Large centered logo for splash/login pages
 */
export function MeridianLogoLarge({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col items-center ${className}`}>
      <motion.div
        whileHover={{
          scale: 1.05,
          transition: { duration: 0.4, ease: "easeInOut" },
        }}
      >
        <MeridianLogo size={72} showText={false} />
      </motion.div>
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.8 }}
        className="mt-4 text-4xl font-bold tracking-tight"
      >
        <span className="logo-text-gradient">Meridian</span>
      </motion.h1>
    </div>
  );
}
