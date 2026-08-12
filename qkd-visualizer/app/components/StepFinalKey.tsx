'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InitializeConnectionResponse } from '../types/initialize_request';

interface StepFinalKeyProps {
  result: InitializeConnectionResponse;
}

// ─── Small helpers ────────────────────────────────────────────────────────────

/** Render two bit-strings side by side with mismatched positions highlighted. */
const BitString: React.FC<{
  bits: string;
  compareTo?: string;
  /** style for mismatched bits on THIS string */
  mismatchClass?: string;
  maxHeight?: string;
}> = ({ bits, compareTo = '', mismatchClass = 'bg-zinc-300 text-zinc-600', maxHeight = 'max-h-24' }) => (
  <div className={`bg-white p-3 rounded-xl border border-zinc-200 font-mono text-xs text-zinc-700 break-all leading-relaxed shadow-inner overflow-y-auto ${maxHeight}`}>
    {bits.split('').map((char, idx) => {
      const isMismatch = compareTo.length > 0 && compareTo[idx] !== undefined && char !== compareTo[idx];
      return (
        <span
          key={idx}
          className={isMismatch ? `${mismatchClass} font-bold px-0.5 rounded` : ''}
        >
          {char}
        </span>
      );
    })}
  </div>
);

/** Section header used throughout. */
const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <h4 className="text-xs font-bold text-zinc-700 uppercase tracking-widest mb-1">{children}</h4>
);

/** Render a single column vector in brackets with slicing. */
const VectorView: React.FC<{
  elements: string[] | number[];
  firstCount: number;
  lastCount: number;
  label: string;
}> = ({ elements, firstCount, lastCount, label }) => {
  const numElements = elements.length;

  const displayIndices: (number | 'ellipsis')[] = [];
  if (numElements <= firstCount + lastCount) {
    for (let i = 0; i < numElements; i++) displayIndices.push(i);
  } else {
    for (let i = 0; i < firstCount; i++) displayIndices.push(i);
    displayIndices.push('ellipsis');
    for (let i = numElements - lastCount; i < numElements; i++) displayIndices.push(i);
  }

  return (
    <div className="flex flex-col items-center shrink-0">
      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2 select-none">
        {label}
      </span>
      <div className="relative border-l-2 border-r-2 border-zinc-500 px-3 py-1 font-mono text-sm bg-white rounded-[4px] flex flex-col items-center justify-center min-w-[2.5rem] shadow-sm select-all">
        {displayIndices.map((idx, rIdx) => {
          if (idx === 'ellipsis') {
            return (
              <span key={`vec-ell-${rIdx}`} className="h-7 flex items-center justify-center text-zinc-400 font-bold select-none">
                ⋮
              </span>
            );
          }
          return (
            <span key={`vec-val-${idx}`} className="h-7 flex items-center justify-center text-black font-bold">
              {elements[idx]}
            </span>
          );
        })}
      </div>
      <span className="text-[9px] text-zinc-400 font-mono mt-1 select-none">
        [{numElements} &times; 1]
      </span>
    </div>
  );
};

/** Render a mathematical equation containing the Toeplitz Matrix multiplication. */
const ToeplitzEquationView: React.FC<{
  matrix?: number[][];
  reconciledBits: string;
  secretFinalKey: string;
}> = ({ matrix, reconciledBits, secretFinalKey }) => {
  if (!matrix || matrix.length === 0 || matrix[0].length === 0) return null;

  const numRows = matrix.length;
  const numCols = matrix[0].length;

  const firstRowsCount = 5;
  const lastRowsCount = 5;
  const firstColsCount = 6;
  const lastColsCount = 6;

  // Determine row indices to display
  const rowIndices: (number | 'ellipsis')[] = [];
  if (numRows <= firstRowsCount + lastRowsCount) {
    for (let i = 0; i < numRows; i++) rowIndices.push(i);
  } else {
    for (let i = 0; i < firstRowsCount; i++) rowIndices.push(i);
    rowIndices.push('ellipsis');
    for (let i = numRows - lastRowsCount; i < numRows; i++) rowIndices.push(i);
  }

  // Determine column indices to display
  const colIndices: (number | 'ellipsis')[] = [];
  if (numCols <= firstColsCount + lastColsCount) {
    for (let j = 0; j < numCols; j++) colIndices.push(j);
  } else {
    for (let j = 0; j < firstColsCount; j++) colIndices.push(j);
    colIndices.push('ellipsis');
    for (let j = numCols - lastColsCount; j < numCols; j++) colIndices.push(j);
  }

  const reconciledArray = reconciledBits.split('').map(Number);
  const secretArray = secretFinalKey.split('').map(Number);

  return (
    <div className="bg-zinc-50 p-6 rounded-xl border border-zinc-200 shadow-inner max-w-full overflow-x-auto">
      <div className="flex flex-col lg:flex-row items-center justify-center gap-6 min-w-max p-2">
        
        {/* 1. Toeplitz Matrix T */}
        <div className="flex flex-col items-center">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2 select-none">
            Toeplitz Matrix (T)
          </span>
          <div className="inline-block border border-zinc-300 rounded-lg overflow-hidden bg-white shadow-sm">
            <table className="table-fixed divide-y divide-zinc-200 border-collapse">
              <tbody>
                {rowIndices.map((rowIndex, rIdx) => {
                  if (rowIndex === 'ellipsis') {
                    return (
                      <tr key={`row-ell-${rIdx}`} className="bg-zinc-50/50">
                        {colIndices.map((_, cIdx) => (
                          <td
                            key={`cell-ell-${rIdx}-${cIdx}`}
                            className="px-2.5 py-1 text-center font-bold text-zinc-400 align-middle leading-none select-none h-7 min-w-[2.2rem]"
                          >
                            ⋮
                          </td>
                        ))}
                      </tr>
                    );
                  }

                  const rowData = matrix[rowIndex];

                  return (
                    <tr key={`row-${rowIndex}`} className="hover:bg-zinc-50/30 transition-colors h-7">
                      {colIndices.map((colIndex, cIdx) => {
                        if (colIndex === 'ellipsis') {
                          return (
                            <td
                              key={`cell-row-ell-${rowIndex}-${cIdx}`}
                              className="px-2.5 py-1 text-center font-bold text-zinc-400 align-middle leading-none select-none min-w-[2.2rem]"
                            >
                              ⋯
                            </td>
                          );
                        }

                        const value = rowData[colIndex];
                        return (
                          <td
                            key={`cell-${rowIndex}-${colIndex}`}
                            className={`px-2.5 py-1 text-center font-bold font-mono min-w-[2.2rem] align-middle ${
                              value === 1 ? 'text-black bg-zinc-100/50' : 'text-zinc-400'
                            }`}
                          >
                            {value}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <span className="text-[9px] text-zinc-400 font-mono mt-1 select-none">
            [{numRows} &times; {numCols}]
          </span>
        </div>

        {/* 2. Matrix Multiplication Sign */}
        <div className="flex flex-col items-center justify-center select-none text-zinc-400 px-2 shrink-0">
          <span className="text-2xl font-bold font-sans">&times;</span>
          <span className="text-[8px] uppercase tracking-wider font-semibold text-zinc-500 whitespace-nowrap">
            Matrix Mult
          </span>
        </div>

        {/* 3. Input Column Vector X (Alice's Reconciled Bits) */}
        <VectorView
          elements={reconciledArray}
          firstCount={firstColsCount}
          lastCount={lastColsCount}
          label="Reconciled Vector (x)"
        />

        {/* 4. Modulo 2 Operation Label */}
        <div className="flex flex-col items-center justify-center select-none text-zinc-400 px-2 shrink-0">
          <span className="text-sm font-mono font-bold">mod 2</span>
          <span className="text-[8px] uppercase tracking-wider font-semibold text-zinc-500 whitespace-nowrap">
            GF(2) Arithmetic
          </span>
        </div>

        {/* 5. Equals Operator */}
        <div className="flex flex-col items-center justify-center select-none text-zinc-400 px-2 shrink-0">
          <span className="text-2xl font-bold font-sans">=</span>
          <span className="text-[8px] uppercase tracking-wider font-semibold text-zinc-500 whitespace-nowrap">
            Yields
          </span>
        </div>

        {/* 6. Output Column Vector Y (Alice's Secret Final Key) */}
        <VectorView
          elements={secretArray}
          firstCount={firstRowsCount}
          lastCount={lastRowsCount}
          label="Secret Final Key (y)"
        />

      </div>
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

export const StepFinalKey: React.FC<StepFinalKeyProps> = ({ result }) => {
  const qberBound = result.qber_bound ?? result.qber;
  const isCompromised = qberBound > 0.11;

  // Key values — prefer the new distributed-Cascade field names, fall back to legacy
  const aliceRaw = result.alice_raw_key ?? result.alice_final_key ?? '';
  const bobRaw = result.bob_raw_key ?? result.bob_final_key ?? '';
  const aliceReconciled = result.alice_reconciled_key ?? aliceRaw;
  const bobReconciled = result.bob_reconciled_key ?? bobRaw;
  const aliceSecret = result.alice_secret_final_key ?? '';
  const bobSecret = result.bob_secret_final_key ?? '';

  const reconcileMatch = result.is_final_key_matched ?? (aliceReconciled === bobReconciled && aliceReconciled !== '');
  const secretMatch = aliceSecret !== '' && bobSecret !== '' && aliceSecret === bobSecret;

  // ── Aborted ────────────────────────────────────────────────────────────────
  if (isCompromised) {
    return (
      <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-zinc-400 border-dashed bg-zinc-50 space-y-6 text-center shadow-sm">
        <div className="w-20 h-20 rounded-full bg-white border border-zinc-300 flex items-center justify-center text-zinc-500">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="space-y-2 max-w-lg">
          <h3 className="text-2xl font-bold text-black tracking-widest uppercase">Protocol Aborted</h3>
          <p className="text-sm text-zinc-500">
            The Serfling QBER bound exceeded the 11% safety threshold — eavesdropper activity detected. Key generation was securely aborted and no data was encrypted.
          </p>
        </div>
      </div>
    );
  }

  // ── Success ─────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 animate-fade-in">

      {/* ── 1. Raw keys ──────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="p-5 rounded-2xl border border-zinc-200 bg-white shadow-sm space-y-4"
      >
        {/* Explanation */}
        <div className="space-y-1">
          <SectionLabel>Step 1 — Raw Sifted Keys</SectionLabel>
          <p className="text-sm text-zinc-500 leading-relaxed">
            These are the <strong className="text-zinc-800">80% of matching-basis bits</strong> that were <em>not</em> sacrificed for the QBER sample check.
            Alice&apos;s copy is noiseless; Bob&apos;s copy may contain bit errors introduced by the quantum channel
            (depolarization, dark counts, or Eve&apos;s interception). Mismatched positions are highlighted below.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Alice raw */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-100 border border-zinc-300 flex items-center justify-center text-black font-bold text-xs">A</div>
              <SectionLabel>Alice&apos;s Raw Key</SectionLabel>
            </div>
            <BitString
              bits={aliceRaw}
              compareTo={bobRaw}
              mismatchClass="bg-zinc-200 text-zinc-500 border border-zinc-400"
            />
            <p className="text-[10px] text-zinc-400 text-right">{aliceRaw.length} bits</p>
          </div>

          {/* Bob raw */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-100 border border-zinc-300 flex items-center justify-center text-black font-bold text-xs">B</div>
              <SectionLabel>Bob&apos;s Raw Key</SectionLabel>
            </div>
            <BitString
              bits={bobRaw}
              compareTo={aliceRaw}
              mismatchClass="bg-black text-white border border-zinc-900"
            />
            <p className="text-[10px] text-zinc-400 text-right">{bobRaw.length} bits</p>
          </div>
        </div>
      </motion.div>

      {/* ── 2. Cascade reconciliation ─────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.15 }}
        className="p-5 rounded-2xl border border-zinc-200 bg-white shadow-sm space-y-4"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <SectionLabel>Step 2 — Cascade Error Reconciliation</SectionLabel>
            <p className="text-sm text-zinc-500 leading-relaxed max-w-xl">
              Bob ran the Cascade protocol, querying Alice&apos;s parity checks over the classical channel to locate and flip erroneous bits — without ever revealing the key itself.
            </p>
          </div>

          {/* Stats pills */}
          {(result.corrections !== undefined || result.leaked_bits !== undefined) && (
            <div className="flex flex-wrap gap-2 shrink-0">
              {result.corrections !== undefined && (
                <span className="px-2.5 py-1 rounded-full border border-zinc-200 bg-zinc-50 text-[10px] font-semibold text-zinc-600 uppercase tracking-wider animate-pulse">
                  {result.corrections} bit{result.corrections !== 1 ? 's' : ''} corrected
                </span>
              )}
              {result.leaked_bits !== undefined && (
                <span className="px-2.5 py-1 rounded-full border border-zinc-200 bg-zinc-50 text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">
                  {result.leaked_bits} bits leaked (parity)
                </span>
              )}
            </div>
          )}
        </div>

        {/* Reconciled key pair */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-100 border border-zinc-300 flex items-center justify-center text-black font-bold text-xs">A</div>
              <SectionLabel>Alice&apos;s Reconciled Key</SectionLabel>
            </div>
            <BitString
              bits={aliceReconciled}
              compareTo={bobReconciled}
              mismatchClass="bg-zinc-200 text-zinc-500 border border-zinc-400"
            />
            <p className="text-[10px] text-zinc-400 text-right">{aliceReconciled.length} bits</p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-100 border border-zinc-300 flex items-center justify-center text-black font-bold text-xs">B</div>
              <SectionLabel>Bob&apos;s Reconciled Key</SectionLabel>
            </div>
            <BitString
              bits={bobReconciled}
              compareTo={aliceReconciled}
              mismatchClass="bg-black text-white border border-zinc-900"
            />
            <p className="text-[10px] text-zinc-400 text-right">{bobReconciled.length} bits</p>
          </div>
        </div>

        {/* Reconciliation status banner */}
        {reconcileMatch ? (
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-zinc-900 text-white text-xs font-semibold">
            <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
            </svg>
            <span>
              Keys are identical after applying Cascade — {result.corrections ?? 0} correction{(result.corrections ?? 0) !== 1 ? 's' : ''} made,
              {' '}{result.leaked_bits ?? 0} parity bits sacrificed to the public channel.
            </span>
          </div>
        ) : (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl border border-zinc-300 border-dashed bg-zinc-50 text-xs text-zinc-700">
            <svg className="w-4 h-4 shrink-0 mt-0.5 text-zinc-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p>
              <strong className="text-zinc-900">Residual mismatch after Cascade.</strong>{' '}
              Cascade&apos;s binary search can only correct blocks with an <em>odd</em> number of errors. Pairs of errors in the
              same block cancel each other&apos;s parity signature and are invisible to the algorithm — a known edge case of the Cascade protocol.
              Set <strong>Depolarization Rate → 0%</strong> and re-run to eliminate channel noise.
            </p>
          </div>
        )}
      </motion.div>

      {/* ── 3. Privacy Amplification & Final Secret Key ───────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="p-5 rounded-2xl border border-zinc-200 bg-white shadow-sm space-y-5"
      >
        <div className="space-y-1">
          <SectionLabel>Step 3 — Privacy Amplification (Toeplitz Hash)</SectionLabel>
          <p className="text-sm text-zinc-500 leading-relaxed">
            The reconciled key is compressed using a random <strong className="text-zinc-800">Toeplitz matrix</strong> (a linear hash over GF(2)).
            This discards all information leaked to Eve during parity checks, producing a shorter key that Eve has negligible
            knowledge of. Both Alice and Bob apply the <em>same</em> shared random seed, so they independently derive
            the identical final secret key without further communication.
          </p>
        </div>

        {/* Dynamic Toeplitz Matrix Equation View */}
        {result.toeplitz_matrix && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <SectionLabel>Matrix Multiplication (T &times; x mod 2 = y)</SectionLabel>
            </div>
            <ToeplitzEquationView
              matrix={result.toeplitz_matrix}
              reconciledBits={aliceReconciled}
              secretFinalKey={aliceSecret}
            />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center text-white font-bold text-xs">A</div>
              <SectionLabel>Alice&apos;s Secret Final Key</SectionLabel>
            </div>
            <BitString bits={aliceSecret} compareTo={bobSecret} mismatchClass="bg-zinc-300 text-zinc-600" maxHeight="max-h-20" />
            <p className="text-[10px] text-zinc-400 text-right">{aliceSecret.length} bits</p>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center text-white font-bold text-xs">B</div>
              <SectionLabel>Bob&apos;s Secret Final Key</SectionLabel>
            </div>
            <BitString bits={bobSecret} compareTo={aliceSecret} mismatchClass="bg-black text-white border border-zinc-900" maxHeight="max-h-20" />
            <p className="text-[10px] text-zinc-400 text-right">{bobSecret.length} bits</p>
          </div>
        </div>

        {/* Final key match badge */}
        {aliceSecret && bobSecret && (
          secretMatch ? (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-zinc-900 text-white text-xs font-semibold shadow-md">
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>
                Encryption complete — Alice and Bob share an identical {aliceSecret.length}-bit secret key.
                The ciphertext was transmitted over the public channel and decrypted successfully by Bob.
              </span>
            </div>
          ) : (
            <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl border border-zinc-300 border-dashed bg-zinc-50 text-xs text-zinc-700">
              <svg className="w-4 h-4 shrink-0 mt-0.5 text-zinc-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p>
                <strong className="text-zinc-900">Secret keys differ.</strong>{' '}
                A residual mismatch in the reconciled key propagates through the Toeplitz hash into an entirely different secret key.
                Decryption by Bob will fail. Set <strong>Depolarization Rate → 0%</strong> to ensure clean key agreement.
              </p>
            </div>
          )
        )}
      </motion.div>

    </div>
  );
};
