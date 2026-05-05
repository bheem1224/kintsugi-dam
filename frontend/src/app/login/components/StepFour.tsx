"use client"

import * as React from "react"
import { motion } from "framer-motion"

export function StepFour() {
  return (
    <div className="flex flex-col items-center justify-center text-center space-y-8 py-12">
      <div className="relative">
        {/* Pulsing glassmorphic glow */}
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute inset-0 bg-gradient-to-tr from-green-500/30 to-blue-500/30 rounded-full blur-[80px]"
        />

        <div className="relative z-10 h-32 w-32 rounded-full bg-black/40 border border-white/10 flex items-center justify-center shadow-2xl backdrop-blur-md">
          <svg
            viewBox="0 0 100 100"
            className="w-20 h-20 text-primary"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <motion.path
              d="M20 50 L45 75 L80 30"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{
                duration: 0.8,
                delay: 0.2,
                ease: "easeOut",
              }}
            />
          </svg>
        </div>
      </div>
      
      <div className="space-y-2 relative z-10">
        <motion.h2
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-5xl font-extrabold tracking-tighter"
        >
          Setup Complete
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-xl text-muted-foreground"
        >
          Kintsugi-DAM is now guarding your digital legacy.
        </motion.p>
      </div>
    </div>
  )
}
