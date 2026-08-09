'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface Step {
  id: string;
  label: string;
  icon: string;
  color: string;
  activeColor: string;
}

interface StepNavigatorProps {
  steps: Step[];
  currentStep: number;
  totalColumns: number;
  maxColumns: number;
  onPrevStep: () => void;
  onNextStep: () => void;
  onPrevCol: () => void;
  onNextCol: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
  canAddCol: boolean;
  canRemoveCol: boolean;
  stepTitle: string;
  stepDescription: string;
}

export const StepNavigator: React.FC<StepNavigatorProps> = ({
  steps,
  currentStep,
  totalColumns,
  maxColumns,
  onPrevStep,
  onNextStep,
  onPrevCol,
  onNextCol,
  canGoBack,
  canGoForward,
  canAddCol,
  canRemoveCol,
  stepTitle,
  stepDescription,
}) => {
  return (
    <div className="space-y-5">
      {/* Step indicators */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {steps.map((step, idx) => {
          const isActive = idx === currentStep;
          const isPast = idx < currentStep;
          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center gap-1 shrink-0">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-base font-bold border transition-all duration-300 ${
                    isActive
                      ? `${step.activeColor} shadow-[0_0_15px_rgba(255,255,255,0.2)] scale-110`
                      : isPast
                      ? 'text-white border-zinc-500 bg-zinc-800'
                      : 'text-zinc-600 border-zinc-800 bg-black'
                  }`}
                >
                  {isPast ? '✓' : step.icon}
                </div>
                <span
                  className={`text-[9px] font-semibold uppercase tracking-widest max-w-[60px] text-center leading-tight ${
                    isActive ? 'text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]' : isPast ? 'text-zinc-400' : 'text-zinc-600'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 min-w-[20px] rounded-full transition-all duration-500 ${
                    idx < currentStep ? 'bg-zinc-500' : 'bg-zinc-900'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Current step title */}
      <motion.div
        key={stepTitle}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-1"
      >
        <p className="text-[11px] font-semibold text-zinc-500 uppercase tracking-widest">
          Step {currentStep + 1} of {steps.length}
        </p>
        <h3 className="text-lg sm:text-xl font-bold text-black">{stepTitle}</h3>
        <p className="text-sm text-zinc-600 leading-relaxed max-w-3xl">{stepDescription}</p>
      </motion.div>

      {/* Column reveal + step nav controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Column reveal controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 font-mono">
            Columns: <span className="text-black font-bold">{totalColumns}</span>/{maxColumns}
          </span>
          <button
            onClick={onPrevCol}
            disabled={!canRemoveCol}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-100 border border-zinc-300 text-zinc-600 hover:text-black hover:border-zinc-400 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            − Col
          </button>
          <button
            onClick={onNextCol}
            disabled={!canAddCol}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-black border border-black text-white hover:bg-zinc-800 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-[0_2px_8px_rgba(0,0,0,0.15)]"
          >
            + Col
          </button>
          {/* Progress bar for columns */}
          <div className="hidden sm:flex items-center gap-1.5">
            {Array.from({ length: maxColumns }).map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i < totalColumns ? 'w-4 bg-zinc-900' : 'w-2 bg-zinc-200'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step navigation */}
        <div className="flex items-center gap-2">
          <motion.button
            onClick={onPrevStep}
            disabled={!canGoBack}
            whileHover={{ scale: canGoBack ? 1.05 : 1 }}
            whileTap={{ scale: canGoBack ? 0.95 : 1 }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-zinc-100 border border-zinc-300 text-zinc-700 hover:bg-zinc-200 hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back</span>
          </motion.button>

          <motion.button
            onClick={onNextStep}
            disabled={!canGoForward}
            whileHover={{ scale: canGoForward ? 1.05 : 1 }}
            whileTap={{ scale: canGoForward ? 0.95 : 1 }}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-bold bg-black text-white hover:bg-zinc-800 shadow-[0_2px_8px_rgba(0,0,0,0.15)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <span>Next Step</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </motion.button>
        </div>
      </div>
    </div>
  );
};
