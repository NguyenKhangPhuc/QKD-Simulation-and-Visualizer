'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { QuantumTable, ColumnDef } from './QuantumTable';
import { InitializeConnectionResponse } from '../types/initialize_request';

interface StepQBERTableProps {
  result: InitializeConnectionResponse;
  visibleColumns: number;
}

export const StepQBERTable: React.FC<StepQBERTableProps> = ({ result, visibleColumns }) => {
  const qberBound = result.qber_bound ?? result.qber;
  const qber = result.qber;
  const isCompromised = qberBound > 0.11;

  const [fillValue, setFillValue] = useState(0);
  useEffect(() => {
    const timeout = setTimeout(() => setFillValue(qberBound * 100), 100);
    return () => clearTimeout(timeout);
  }, [qberBound]);

  const rows = result.sample_indices_qber.map((origIdx, i) => {
    const aliceBit = result.sample_bits_qber[i];
    const bobBit = result.initial_bob_bits[origIdx];
    return { origIdx, aliceBit, bobBit, isMatch: aliceBit === bobBit };
  });

  const columns: ColumnDef<typeof rows[0]>[] = [
    {
      key: 'origIdx',
      header: 'Index',
      render: (row) => <span className="text-zinc-500">#{row.origIdx}</span>,
    },
    {
      key: 'aliceBit',
      header: 'Alice Bit',
      render: (row) => <span className="font-bold text-black">{row.aliceBit}</span>,
    },
    {
      key: 'bobBit',
      header: 'Bob Bit',
      render: (row) => <span className="font-bold text-black">{row.bobBit}</span>,
    },
    {
      key: 'match',
      header: 'Result',
      render: (row) =>
        row.isMatch ? (
          <span className="px-2 py-0.5 rounded bg-black text-white text-xs font-bold border border-black shadow-sm">
            ✓ Match
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded bg-zinc-100 text-zinc-500 text-xs font-bold border border-zinc-300 border-dashed">
            ✗ Error
          </span>
        ),
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <QuantumTable
          rows={rows}
          columns={columns}
          caption="QBER Sample Verification"
          totalCount={rows.length}
          borderClass={isCompromised ? 'border-zinc-400 border-dashed' : 'border-zinc-300'}
          headerBgClass={isCompromised ? 'bg-zinc-100' : 'bg-zinc-50'}
          visibleColumns={visibleColumns}
        />
      </div>

      <div className="space-y-4">
        <div className={`p-6 rounded-2xl border backdrop-blur-md ${isCompromised ? 'bg-zinc-50 border-zinc-400 border-dashed' : 'bg-white border-zinc-300 shadow-sm'}`}>
          {/* Header */}
          <div className="flex justify-between items-center mb-5">
            <h4 className="font-bold text-black uppercase tracking-widest text-sm">QBER Analysis</h4>
            <span className={`px-3 py-1 text-[10px] font-bold uppercase tracking-widest rounded-full border ${
              isCompromised
                ? 'bg-zinc-100 text-zinc-600 border-zinc-400 border-dashed'
                : 'bg-black text-white border-black shadow-sm'
            }`}>
              {isCompromised ? 'Eavesdropper Detected' : 'Secure Channel'}
            </span>
          </div>

          {/* Primary: QBER Bound gauge */}
          <div className="mb-1">
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-xs font-semibold text-zinc-700 uppercase tracking-wider">
                QBER Bound <span className="text-[10px] font-normal text-zinc-400">(Serfling upper bound — decision metric)</span>
              </span>
              <span className={`text-lg font-bold font-mono ${isCompromised ? 'text-zinc-600' : 'text-black'}`}>
                {(qberBound * 100).toFixed(2)}%
              </span>
            </div>
            <div className="relative h-4 rounded-full bg-zinc-100 border border-zinc-200 overflow-hidden mb-1">
              <motion.div
                className={`absolute top-0 left-0 h-full ${isCompromised ? 'bg-zinc-400' : 'bg-black'}`}
                initial={{ width: '0%' }}
                animate={{ width: `${Math.min(fillValue, 100)}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
              {/* 11% threshold marker */}
              <div className="absolute top-0 bottom-0 left-[11%] w-0.5 bg-zinc-500 z-10" />
            </div>
            <div className="flex justify-between text-[10px] text-zinc-400 font-mono">
              <span>0%</span>
              <span className="text-zinc-600 font-semibold">11% safety threshold</span>
              <span>100%</span>
            </div>
          </div>

          {/* Secondary: raw QBER */}
          <div className="mt-4 px-3 py-2.5 rounded-xl bg-zinc-50 border border-zinc-200 flex items-center justify-between">
            <div>
              <p className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">Raw QBER</p>
              <p className="text-[10px] text-zinc-400">
                Measured directly from the {result.sample_size_qber}-bit sample. Used as input to Serfling.
              </p>
            </div>
            <span className="text-base font-bold font-mono text-zinc-600">{(qber * 100).toFixed(2)}%</span>
          </div>

          {/* Stats grid */}
          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className="text-xl font-bold text-black">{result.sample_size_qber}</div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Sample Size</div>
            </div>
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className={`text-xl font-bold ${result.mismatches && result.mismatches > 0 ? 'text-zinc-600' : 'text-black'}`}>
                {result.mismatches !== undefined ? result.mismatches : Math.round(qber * result.sample_size_qber)}
              </div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Mismatches</div>
            </div>
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className={`text-xl font-bold ${isCompromised ? 'text-zinc-500' : 'text-black'}`}>
                {(qberBound * 100).toFixed(2)}%
              </div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">QBER Bound</div>
            </div>
          </div>
        </div>

        {/* Explanation card */}
        <div className="px-4 py-3 rounded-xl border border-zinc-200 bg-zinc-50 text-[11px] text-zinc-500 leading-relaxed">
          <strong className="text-zinc-700">Why use QBER Bound?</strong> The raw QBER is a point estimate subject to sampling noise.
          The Serfling upper bound provides a statistically conservative estimate — with high probability (1&nbsp;−&nbsp;ε), the true
          channel error rate does not exceed this value, making it the correct metric for the security decision.
        </div>
      </div>
    </div>
  );
};
