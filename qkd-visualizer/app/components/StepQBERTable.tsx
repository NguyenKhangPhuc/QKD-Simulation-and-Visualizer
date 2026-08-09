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
  const [fillValue, setFillValue] = useState(0);

  useEffect(() => {
    // Animate gauge on mount
    const timeout = setTimeout(() => {
      setFillValue(result.qber * 100);
    }, 100);
    return () => clearTimeout(timeout);
  }, [result.qber]);

  const qberPercent = (result.qber * 100).toFixed(2);
  const isCompromised = result.qber > 0.11;

  const rows = result.sample_indices_qber.map((origIdx, i) => {
    const aliceBit = result.sample_bits_qber[i];
    const bobBit = result.initial_bob_bits[origIdx];
    return {
      origIdx,
      aliceBit,
      bobBit,
      isMatch: aliceBit === bobBit,
    };
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

      <div className="space-y-6">
        <div className={`p-6 rounded-2xl border backdrop-blur-md ${isCompromised ? 'bg-zinc-50 border-zinc-400 border-dashed' : 'bg-white border-zinc-300 shadow-sm'}`}>
          <div className="flex justify-between items-center mb-6">
            <h4 className="font-bold text-black uppercase tracking-widest">Error Rate (QBER)</h4>
            <span className={`px-3 py-1 text-[10px] font-bold uppercase tracking-widest rounded-full border ${
              isCompromised ? 'bg-zinc-100 text-zinc-600 border-zinc-400 border-dashed' : 'bg-black text-white border-black shadow-sm'
            }`}>
              {isCompromised ? 'Eavesdropper Detected' : 'Secure Channel'}
            </span>
          </div>

          <div className="relative h-4 rounded-full bg-zinc-100 border border-zinc-200 overflow-hidden mb-2">
            <motion.div
              className={`absolute top-0 left-0 h-full ${isCompromised ? 'bg-zinc-400' : 'bg-black'}`}
              initial={{ width: '0%' }}
              animate={{ width: `${Math.min(fillValue, 100)}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
            {/* 11% Threshold Marker */}
            <div className="absolute top-0 bottom-0 left-[11%] w-0.5 bg-black z-10" />
          </div>
          <div className="flex justify-between text-xs text-zinc-400 font-mono">
            <span>0%</span>
            <span className="text-black font-semibold">11% Threshold</span>
            <span>100%</span>
          </div>

          <div className="mt-8 grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className="text-2xl font-bold text-black">{result.sample_size_qber}</div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Sample Size</div>
            </div>
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className={`text-2xl font-bold ${result.mismatches ? (result.mismatches > 0 ? 'text-zinc-600' : 'text-black') : 'text-black'}`}>
                {result.mismatches !== undefined ? result.mismatches : (result.qber * result.sample_size_qber).toFixed(0)}
              </div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Mismatches</div>
            </div>
            <div className="text-center p-3 rounded-xl bg-zinc-50 border border-zinc-200">
              <div className={`text-2xl font-bold ${isCompromised ? 'text-zinc-500' : 'text-black drop-shadow-sm'}`}>
                {qberPercent}%
              </div>
              <div className="text-[10px] text-zinc-500 uppercase tracking-widest">QBER</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
