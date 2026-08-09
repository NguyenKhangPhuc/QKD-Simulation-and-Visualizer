'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { initializeConnection } from '../service';
import { InitializeConnectionResponse } from '../types/initialize_request';
import { gradients, shadow } from '../constants/design-tokens';

import { StepNavigator } from './StepNavigator';
import { StepAliceTable } from './StepAliceTable';
import { StepEveTable } from './StepEveTable';
import { StepBobTable } from './StepBobTable';
import { StepSiftingTable } from './StepSiftingTable';
import { StepQBERTable } from './StepQBERTable';
import { StepFinalKey } from './StepFinalKey';

interface QkdVisualizerSectionProps {
  isEve: boolean;
  setIsEve: (eve: boolean) => void;
}

const STEPS = [
  { id: 'alice', label: 'Alice', icon: 'A', color: 'text-zinc-700', activeColor: 'bg-white text-black border-zinc-400' },
  { id: 'eve', label: 'Eve', icon: 'E', color: 'text-zinc-800', activeColor: 'bg-zinc-50 text-black border-zinc-500 border-dashed' },
  { id: 'bob', label: 'Bob', icon: 'B', color: 'text-zinc-700', activeColor: 'bg-white text-black border-zinc-400' },
  { id: 'sifting', label: 'Sifting', icon: 'S', color: 'text-zinc-700', activeColor: 'bg-white text-black border-zinc-400' },
  { id: 'qber', label: 'QBER', icon: 'Q', color: 'text-zinc-700', activeColor: 'bg-white text-black border-zinc-400' },
  { id: 'key', label: 'Key', icon: 'K', color: 'text-zinc-700', activeColor: 'bg-white text-black border-zinc-400' },
];

const STEP_CONTENT = [
  {
    title: "Alice's State Preparation",
    desc: "Alice generates random bits and encodes each qubit into computational |0⟩, |1⟩ (Z-basis) or diagonal |+⟩, |-⟩ (X-basis).",
  },
  {
    title: "Eve's Interception (Eavesdropping)",
    desc: "Eve intercepts and measures each qubit in a random basis, collapsing the quantum state and causing ~25% disturbance.",
  },
  {
    title: "Bob's Measurement",
    desc: "Bob randomly selects a measurement basis for each qubit. Without knowing Alice's basis, he guesses correctly ~50% of the time.",
  },
  {
    title: "Classical Basis Sifting",
    desc: "Alice and Bob publicly compare their basis choices. Only qubits where both chose the same basis form the raw sifted key.",
  },
  {
    title: "QBER Verification",
    desc: "Alice reveals 20% of the sifted key publicly. They compare these sample bits. If more than 11% are wrong, Eve is detected.",
  },
  {
    title: "Final Shared Secret",
    desc: "The final cryptographic key is derived from the remaining 80% of matching indices. These bits are never revealed publicly.",
  },
];

export const QkdVisualizerSection: React.FC<QkdVisualizerSectionProps> = ({
  isEve,
  setIsEve,
}) => {
  const [numBits, setNumBits] = useState<number>(500);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InitializeConnectionResponse | null>(null);
  
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = backward
  const [visibleColumns, setVisibleColumns] = useState(8);

  const steps = isEve ? STEPS : STEPS.filter((s) => s.id !== 'eve');
  const stepContent = isEve ? STEP_CONTENT : STEP_CONTENT.filter((_, i) => i !== 1);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setVisibleColumns(8);
    try {
      const data = await initializeConnection({
        num_bits: Number(numBits),
        is_eve: isEve,
      });
      setResult(data);
    } catch (err: unknown) {
      console.error(err);
      setError('Failed to connect to Alice client server (localhost:8001). Please ensure python3 alice_client.py is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = () => {
    if (currentStep < steps.length - 1) {
      setDirection(1);
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 0) {
      setDirection(-1);
      setCurrentStep(currentStep - 1);
    }
  };

  const currentStepId = steps[currentStep].id;

  const renderStep = () => {
    if (!result) return null;
    switch (currentStepId) {
      case 'alice': return <StepAliceTable result={result} visibleColumns={visibleColumns} />;
      case 'eve': return <StepEveTable result={result} visibleColumns={visibleColumns} />;
      case 'bob': return <StepBobTable result={result} visibleColumns={visibleColumns} />;
      case 'sifting': return <StepSiftingTable result={result} visibleColumns={visibleColumns} />;
      case 'qber': return <StepQBERTable result={result} visibleColumns={visibleColumns} />;
      case 'key': return <StepFinalKey result={result} />;
      default: return null;
    }
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!result) return;
      if (e.key === 'ArrowRight') handleNextStep();
      if (e.key === 'ArrowLeft') handlePrevStep();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [result, currentStep]);

  return (
    <section id="pkd-visualizer" className="relative py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-white">
      {/* Section Header */}
      <div className="text-center mb-12">
        <motion.h2
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-3xl sm:text-5xl font-bold text-black tracking-tight"
        >
          Quantum Key Distribution{' '}
          <span className="text-zinc-500">Settings</span>
        </motion.h2>
        <p className="mt-3 text-zinc-600 text-sm sm:text-base max-w-2xl mx-auto">
          Configure quantum parameters, execute the BB84 protocol via REST endpoints, and inspect state collapse step-by-step.
        </p>
      </div>

      {/* Control Panel Form Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xl mb-12"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Input 1: Number of Bits */}
            <div>
              <label className="block text-xs font-semibold text-zinc-700 uppercase tracking-wider mb-2">
                Number of Qubits to Generate
              </label>
              <div className="space-y-3">
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="50"
                    max="1000"
                    step="50"
                    value={numBits}
                    onChange={(e) => setNumBits(Number(e.target.value))}
                    className="w-full h-2 bg-zinc-200 border border-zinc-300 rounded-lg appearance-none cursor-pointer accent-black"
                  />
                  <input
                    type="number"
                    min="10"
                    max="2000"
                    value={numBits}
                    onChange={(e) => setNumBits(Number(e.target.value))}
                    className="w-24 px-3 py-2 bg-white border border-zinc-300 rounded-xl text-black font-mono text-center font-bold focus:outline-none focus:border-zinc-500 shadow-sm"
                  />
                </div>
                {/* Presets */}
                <div className="flex gap-2">
                  {[100, 300, 500, 1000].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setNumBits(preset)}
                      className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                        numBits === preset
                          ? 'bg-zinc-100 text-black border border-zinc-400 shadow-sm'
                          : 'bg-white text-zinc-500 hover:text-zinc-700 border border-zinc-200'
                      }`}
                    >
                      {preset} bits
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Input 2: Eve Interception Toggle */}
            <div>
              <label className="block text-xs font-semibold text-zinc-700 uppercase tracking-wider mb-2">
                Eavesdropper Interception (Eve)
              </label>
              <div className="grid grid-cols-2 gap-3 h-[42px]">
                <button
                  type="button"
                  onClick={() => setIsEve(false)}
                  className={`flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all border ${
                    !isEve
                      ? 'bg-zinc-50 text-black border-zinc-400 shadow-sm'
                      : 'bg-white text-zinc-500 border-zinc-200 hover:text-zinc-700 hover:bg-zinc-50'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${!isEve ? 'bg-black' : 'bg-zinc-300'}`} />
                  <span>Secure (No Eve)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsEve(true)}
                  className={`flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all border ${
                    isEve
                      ? 'bg-zinc-100 text-black border-zinc-500 border-dashed shadow-sm'
                      : 'bg-white text-zinc-500 border-zinc-200 hover:text-zinc-700 hover:bg-zinc-50'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${isEve ? 'bg-black animate-pulse' : 'bg-zinc-300'}`} />
                  <span>Eavesdropper (Eve)</span>
                </button>
              </div>
              <p className="mt-3 text-xs text-zinc-500">
                {isEve
                  ? 'Eve performs intercept-resend attacks in random bases before Bob measures.'
                  : 'Quantum states pass directly from Alice to Bob without disturbance.'}
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className={`w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-white text-sm ${gradients.cyanButton} transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-md`}
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Executing BB84 Simulation...</span>
                </>
              ) : (
                <>
                  <span>Execute BB84 Simulation</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 rounded-xl bg-zinc-50 border border-zinc-300 border-dashed text-zinc-800 text-sm font-medium"
          >
            {error}
          </motion.div>
        )}
      </motion.div>

      {/* Results Dashboard - Step Orchestrator */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          {/* Step Navigator */}
          <div className="p-6 rounded-2xl border border-zinc-200 bg-white shadow-sm">
            <StepNavigator
              steps={steps}
              currentStep={currentStep}
              totalColumns={visibleColumns}
              maxColumns={12}
              onPrevStep={handlePrevStep}
              onNextStep={handleNextStep}
              onPrevCol={() => setVisibleColumns((c) => Math.max(1, c - 1))}
              onNextCol={() => setVisibleColumns((c) => Math.min(12, c + 1))}
              canGoBack={currentStep > 0}
              canGoForward={currentStep < steps.length - 1}
              canAddCol={visibleColumns < 12 && currentStepId !== 'key'}
              canRemoveCol={visibleColumns > 1 && currentStepId !== 'key'}
              stepTitle={stepContent[currentStep].title}
              stepDescription={stepContent[currentStep].desc}
            />
          </div>

          {/* Step Content */}
          <div className="relative min-h-[500px] overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-50 p-4 sm:p-6 shadow-inner">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={currentStep}
                custom={direction}
                initial={{ opacity: 0, x: direction > 0 ? 60 : -60 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: direction > 0 ? -60 : 60 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="w-full h-full"
              >
                {renderStep()}
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </section>
  );
};
