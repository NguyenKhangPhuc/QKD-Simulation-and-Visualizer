'use client';

import React from 'react';
import { QuantumTable, ColumnDef } from './QuantumTable';
import { colors } from '../constants/design-tokens';
import { InitializeConnectionResponse } from '../types/initialize_request';

interface StepSiftingTableProps {
  result: InitializeConnectionResponse;
  visibleColumns: number;
}

export const StepSiftingTable: React.FC<StepSiftingTableProps> = ({ result, visibleColumns }) => {
  // Table 1: Basis Comparison
  const basisRows = result.initial_alice_bases.map((aliceBasis, idx) => {
    const bobBasis = result.initial_bob_bases[idx];
    return {
      idx,
      aliceBasis,
      bobBasis,
      isMatch: aliceBasis === bobBasis,
    };
  });

  const basisCols: ColumnDef<typeof basisRows[0]>[] = [
    {
      key: 'idx',
      header: '#',
      render: (row) => <span className="text-zinc-500">#{row.idx}</span>,
    },
    {
      key: 'alice',
      header: 'Alice Basis',
      render: (row) => (
        <span className="text-zinc-500">
          {row.aliceBasis === 0 ? '0 (Z)' : '1 (X)'}
        </span>
      ),
    },
    {
      key: 'bob',
      header: 'Bob Basis',
      render: (row) => (
        <span className="text-zinc-500">
          {row.bobBasis === 0 ? '0 (Z)' : '1 (X)'}
        </span>
      ),
    },
    {
      key: 'match',
      header: 'Match?',
      render: (row) =>
        row.isMatch ? (
          <span className="px-2 py-0.5 rounded bg-black text-white text-xs font-bold border border-black shadow-sm">
            =
          </span>
        ) : (
          <span className="px-2 py-0.5 rounded bg-zinc-100 text-zinc-500 text-xs font-bold border border-zinc-300">
            ≠
          </span>
        ),
    },
  ];

  // Table 2: Matching Indices Bits
  const matchRows = result.matching_indices_alice_bob.map((origIdx) => ({
    origIdx,
    aliceBit: result.initial_alice_bits[origIdx],
    bobBit: result.initial_bob_bits[origIdx],
  }));

  const matchCols: ColumnDef<typeof matchRows[0]>[] = [
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
      render: (row) => <span className="font-bold text-zinc-700">{row.bobBit}</span>,
    },
  ];

  const retentionRate = ((result.matching_indices_alice_bob.length / result.initial_alice_bits.length) * 100).toFixed(0);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <QuantumTable
          rows={basisRows}
          columns={basisCols}
          caption="Basis Comparison"
          totalCount={basisRows.length}
          borderClass="border-zinc-300"
          headerBgClass="bg-zinc-50"
          visibleColumns={visibleColumns}
        />
        <div className="p-4 rounded-xl border border-zinc-200 bg-white text-sm text-zinc-600 shadow-sm">
          Alice and Bob share their bases publicly. If they match, the bit is kept.
        </div>
      </div>

      <div className="space-y-4">
        <QuantumTable
          rows={matchRows}
          columns={matchCols}
          caption="Raw Sifted Key Bits"
          totalCount={matchRows.length}
          borderClass="border-zinc-300" 
          headerBgClass="bg-white"
          visibleColumns={visibleColumns}
        />
        <div className="flex items-center justify-between p-4 rounded-xl border border-zinc-300 bg-white text-sm text-black shadow-sm">
          <span className="text-zinc-600">Retention Rate:</span>
          <span className="font-bold text-lg">{retentionRate}%</span>
        </div>
      </div>
    </div>
  );
};
