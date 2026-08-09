'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InitializeConnectionResponse } from '../types/initialize_request';

interface StepFinalKeyProps {
  result: InitializeConnectionResponse;
}

export const StepFinalKey: React.FC<StepFinalKeyProps> = ({ result }) => {
  const isCompromised = result.qber > 0.11;

  if (isCompromised) {
    return (
      <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-zinc-400 border-dashed bg-zinc-50 backdrop-blur-md space-y-6 text-center shadow-sm">
        <div className="w-20 h-20 rounded-full bg-white border border-zinc-300 flex items-center justify-center text-zinc-500">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="space-y-2 max-w-lg">
          <h3 className="text-2xl font-bold text-black tracking-widest uppercase">Protocol Aborted</h3>
          <p className="text-sm text-zinc-500">
            Eavesdropper detected on the quantum channel. The key generation process has been securely aborted to prevent data compromise. No data was encrypted.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="p-6 rounded-2xl border border-zinc-200 bg-white backdrop-blur-md text-center max-w-3xl mx-auto space-y-3 shadow-sm">
        <h3 className="text-lg font-bold text-black uppercase tracking-widest">Deriving the Shared Secret</h3>
        <p className="text-sm text-zinc-500">
          The QBER check passed successfully. Alice and Bob discard the 20% of bits used for error checking. 
          The remaining <strong className="text-black drop-shadow-sm">80% of matching bits</strong> become the final shared secret key.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Alice Key */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50 space-y-4 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-white border border-zinc-300 flex items-center justify-center text-black font-bold shadow-sm">A</div>
            <h4 className="font-bold text-black uppercase tracking-widest text-sm">Alice&apos;s Final Key</h4>
          </div>
          <div className="bg-white p-4 rounded-xl border border-zinc-200 font-mono text-sm text-zinc-700 break-all leading-relaxed shadow-inner overflow-hidden max-h-32">
            {result.alice_final_key}
          </div>
          <p className="text-xs text-zinc-400 text-right">
            Length: {result.alice_final_key?.length || 0} bits
          </p>
        </motion.div>

        {/* Bob Key */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="p-6 rounded-2xl border border-zinc-200 bg-zinc-50 space-y-4 shadow-sm"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-white border border-zinc-300 flex items-center justify-center text-black font-bold shadow-sm">B</div>
            <h4 className="font-bold text-black uppercase tracking-widest text-sm">Bob&apos;s Final Key</h4>
          </div>
          <div className="bg-white p-4 rounded-xl border border-zinc-200 font-mono text-sm text-zinc-700 break-all leading-relaxed shadow-inner overflow-hidden max-h-32">
            {result.bob_final_key}
          </div>
          <p className="text-xs text-zinc-400 text-right">
            Length: {result.bob_final_key?.length || 0} bits
          </p>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.8 }}
        className="mt-8 p-6 rounded-2xl border border-zinc-300 bg-white text-center space-y-4 shadow-sm"
      >
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-zinc-50 border border-zinc-300 text-black shadow-sm mb-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h4 className="text-lg font-bold text-black tracking-widest uppercase">Encryption Complete</h4>
        <p className="text-sm text-zinc-500 max-w-2xl mx-auto">
          The final bits were hashed via SHA-256 and used to instantiate a symmetric cipher. 
          Alice successfully sent the ciphertext, and Bob successfully decrypted it using his identical key.
        </p>
      </motion.div>
    </div>
  );
};
