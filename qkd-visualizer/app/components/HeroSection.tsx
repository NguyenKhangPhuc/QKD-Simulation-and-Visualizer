'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { gradients, shadow } from '../constants/design-tokens';

export const HeroSection: React.FC = () => {
  const handleScrollToVisualizer = () => {
    const el = document.getElementById('pkd-visualizer');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative min-h-[85vh] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-16 overflow-hidden bg-white">
      {/* Background Animated Light Orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
            x: [0, 40, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-20 -left-20 w-96 h-96 rounded-full bg-zinc-100 blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.3, 0.6, 0.3],
            x: [0, -50, 0],
            y: [0, 40, 0],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/3 -right-20 w-96 h-96 rounded-full bg-zinc-200 blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -bottom-10 left-1/3 w-80 h-80 rounded-full bg-zinc-100 blur-3xl"
        />

        {/* Minimal Grid Mesh Light */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(0,0,0,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:4rem_4rem]" />
      </div>

      {/* Hero Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.1 }}
        className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-center tracking-tight text-black max-w-5xl leading-tight sm:leading-none mt-10"
      >
        Visualize{' '}
        <span className={`bg-gradient-to-r ${gradients.heroText} bg-clip-text text-transparent drop-shadow-sm`}>
          Quantum Key Distribution
        </span>
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="mt-6 text-base sm:text-lg lg:text-xl text-zinc-600 text-center max-w-3xl leading-relaxed"
      >
        Experience how quantum mechanics creates unbreakable security. See how qubits are encoded, how measuring them changes their state, and how eavesdroppers are always caught.
      </motion.p>

      {/* Interactive Quick Configuration Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        className={`mt-12 w-full max-w-md rounded-2xl border border-zinc-200 bg-white/80 backdrop-blur-xl p-8 ${shadow.cyanGlow}`}
      >
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-bold text-black mb-2">Ready to explore?</h3>
            <p className="text-sm text-zinc-500">Configure your simulation settings and watch the BB84 protocol run step-by-step.</p>
          </div>

          {/* Scroll Navigation CTA Button */}
          <div className="pt-2 flex justify-center">
            <button
              onClick={handleScrollToVisualizer}
              className={`w-full px-8 py-4 rounded-xl text-white font-bold text-base ${gradients.cyanButton} shadow-md transition-all transform hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-3`}
            >
              <span>Go to Settings</span>
              <svg
                className="w-5 h-5 animate-bounce"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M19 14l-7 7m0 0l-7-7m7 7V3"
                />
              </svg>
            </button>
          </div>
        </div>
      </motion.div>
    </section>
  );
};
