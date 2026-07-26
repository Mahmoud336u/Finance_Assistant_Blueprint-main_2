"use client";

import { motion, useReducedMotion } from "framer-motion";

interface MeridianLogoProps {
  size?: number;
  collapsed?: boolean;
  showText?: boolean;
  textSize?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export function MeridianLogo({
  size = 32,
  collapsed = false,
  showText = true,
  textSize = "md",
  className = "",
}: MeridianLogoProps) {
  const shouldReduceMotion = useReducedMotion();

  const textSizes = {
    sm: "text-base",
    md: "text-lg",
    lg: "text-2xl",
    xl: "text-4xl",
  };

  // Hover animations
  const logoHover = shouldReduceMotion ? {} : {
    scale: 1.05,
    transition: { duration: 0.3, ease: "easeOut" }
  };

  const starHover = shouldReduceMotion ? {} : {
    y: -2,
    scale: 1.1,
    filter: "drop-shadow(0px 2px 4px rgba(244, 63, 94, 0.5))",
    transition: { duration: 0.3, ease: "easeOut" }
  };

  const pathHover = shouldReduceMotion ? {} : {
    strokeWidth: 3.5,
    filter: "drop-shadow(0px 2px 4px rgba(245, 158, 11, 0.3))",
    transition: { duration: 0.3, ease: "easeOut" }
  };

  return (
    <div className={`flex items-center gap-3 group cursor-pointer ${className}`}>
      <motion.div
        className="relative shrink-0 flex items-center justify-center"
        initial="initial"
        animate="animate"
        whileHover="hover"
        whileTap="tap"
        variants={{
          hover: logoHover,
          tap: { scale: 0.95 }
        }}
      >
        {/* Ambient subtle background glow on hover */}
        <div 
          className="absolute inset-0 rounded-full bg-gradient-to-tr from-amber-500/0 via-rose-500/0 to-violet-500/0 group-hover:from-amber-500/15 group-hover:via-rose-500/15 group-hover:to-violet-500/15 transition-colors duration-500 blur-md pointer-events-none"
          style={{ width: size * 1.5, height: size * 1.5, top: -size * 0.25, left: -size * 0.25 }}
        />

        <svg
          width={size}
          height={size}
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10"
        >
          <defs>
            <linearGradient id="brandGradient" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#F59E0B" /> {/* Amber 500 */}
              <stop offset="50%" stopColor="#F43F5E" /> {/* Rose 500 */}
              <stop offset="100%" stopColor="#8B5CF6" /> {/* Violet 500 */}
            </linearGradient>
            
            <linearGradient id="starGradient" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#F43F5E" /> {/* Rose 500 */}
              <stop offset="100%" stopColor="#8B5CF6" /> {/* Violet 500 */}
            </linearGradient>
          </defs>

          {/* The Meridian Star */}
          <motion.circle 
            cx="16" 
            cy="8" 
            r="3.5" 
            fill="url(#starGradient)"
            variants={{
              initial: shouldReduceMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0 },
              animate: { 
                opacity: 1, 
                scale: 1,
                transition: { duration: 0.5, delay: 0.4, type: "spring", stiffness: 200 }
              },
              hover: starHover
            }}
          />
          
          {/* The Path / M */}
          <motion.path 
            d="M 4 24 L 10 12 L 16 18 L 22 12 L 28 24" 
            stroke="url(#brandGradient)" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round"
            variants={{
              initial: shouldReduceMotion ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 },
              animate: { 
                pathLength: 1, 
                opacity: 1,
                transition: { duration: 1, ease: "easeInOut" }
              },
              hover: pathHover
            }}
          />
        </svg>
      </motion.div>

      {/* Text */}
      {showText && !collapsed && (
        <motion.span
          initial={shouldReduceMotion ? { opacity: 1, x: 0 } : { opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          exit={shouldReduceMotion ? { opacity: 0, x: 0 } : { opacity: 0, x: -8 }}
          transition={{ duration: 0.2 }}
          className={`font-bold tracking-tight text-foreground ${textSizes[textSize]}`}
        >
          Meridian
        </motion.span>
      )}
    </div>
  );
}

export function MeridianLogoLarge({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col items-center group cursor-pointer ${className}`}>
      <MeridianLogo size={80} showText={false} />
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.8 }}
        className="mt-6 text-4xl font-bold tracking-tight"
      >
        <span className="bg-gradient-to-r from-amber-500 via-rose-500 to-violet-500 bg-clip-text text-transparent">
          Meridian
        </span>
      </motion.h1>
    </div>
  );
}
