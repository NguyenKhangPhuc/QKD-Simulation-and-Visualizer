'use client';

import React from 'react';
import { QuantumTable, ColumnDef } from './QuantumTable';
import { colors } from '../constants/design-tokens';
import { InitializeConnectionResponse } from '../types/initialize_request';
import { getQubitState } from './StepAliceTable';

interface StepEveTableProps {
  result: InitializeConnectionResponse;
  visibleColumns: number;
}

export const StepEveTable: React.FC<StepEveTableProps> = ({ result, visibleColumns }) => {
  const eveMeasuredBits = result.eve_measured_bits || [];
  const eveBases = result.eve_bases || [];
  
  const rows = eveMeasuredBits.map((measuredBit, idx) => ({
    idx,
    aliceBasis: result.initial_alice_bases[idx],
    basis: eveBases[idx],
    measuredBit,
  }));

  const columns: ColumnDef<typeof rows[0]>[] = [
    {
      key: 'idx',
      header: '#',
      render: (row) => <span className="text-zinc-500">#{row.idx}</span>,
    },
    {
      key: 'aliceBasis',
      header: 'Alice Basis',
      render: (row) => (
        <span className="text-zinc-400">
          {row.aliceBasis === 0 ? '0 (Z)' : '1 (X)'}
        </span>
      ),
    },
    {
      key: 'basis',
      header: 'Eve Basis',
      render: (row) => {
        const isMatch = row.basis === row.aliceBasis;
        return (
          <span className={isMatch ? 'font-bold text-black' : 'text-zinc-500'}>
            {row.basis === 0 ? '0 (Z)' : '1 (X)'}
          </span>
        );
      },
    },
    {
      key: 'decode',
      header: 'Decode Gate',
      render: (row) => (
        <span className="px-2 py-0.5 rounded bg-zinc-100 text-zinc-700 text-[10px] font-mono border border-zinc-200">
          {row.basis === 1 ? 'H' : '—'}
        </span>
      ),
    },
    {
      key: 'measured',
      header: 'Measured Bit',
      render: (row) => {
        const isMismatchedBasis = row.basis !== row.aliceBasis;
        return (
          <span className={`font-bold ${isMismatchedBasis ? 'text-zinc-500' : 'text-black'}`}>
            {row.measuredBit}
          </span>
        );
      },
    },
    {
      key: 'state',
      header: 'Re-encoded State',
      render: (row) => {
        const state = getQubitState(row.measuredBit, row.basis);
        const isMismatchedBasis = row.basis !== row.aliceBasis;
        return (
          <span className={`font-bold ${isMismatchedBasis ? 'text-zinc-500 bg-zinc-50 border-zinc-300 border-dashed' : 'text-black bg-white border-zinc-400'} px-2 py-0.5 rounded border shadow-sm`}>
            {state}
          </span>
        );
      },
    },
  ];

  return (
    <QuantumTable
      rows={rows}
      columns={columns}
      caption="Eve's Interception & Resend"
      totalCount={rows.length}
      borderClass={colors.step.eve.border}
      headerBgClass={colors.step.eve.headerBg}
      visibleColumns={visibleColumns}
    />
  );
};
