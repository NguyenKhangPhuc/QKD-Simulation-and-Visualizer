'use client';

import React from 'react';
import { QuantumTable, ColumnDef } from './QuantumTable';
import { colors } from '../constants/design-tokens';
import { InitializeConnectionResponse } from '../types/initialize_request';
import { getQubitState } from './StepAliceTable';

interface StepBobTableProps {
  result: InitializeConnectionResponse;
  visibleColumns: number;
}

export const StepBobTable: React.FC<StepBobTableProps> = ({ result, visibleColumns }) => {
  const rows = result.initial_bob_bits.map((measuredBit, idx) => ({
    idx,
    basis: result.initial_bob_bases[idx],
    measuredBit,
    state: getQubitState(measuredBit, result.initial_bob_bases[idx]),
  }));

  const columns: ColumnDef<typeof rows[0]>[] = [
    {
      key: 'idx',
      header: '#',
      render: (row) => <span className="text-zinc-500">#{row.idx}</span>,
    },
    {
      key: 'incoming',
      header: 'Incoming State',
      render: () => (
        <span className="text-zinc-400 italic">Hidden</span>
      ),
    },
    {
      key: 'basis',
      header: 'Bob Basis',
      render: (row) => (
        <span className={row.basis === 0 ? 'text-zinc-800' : 'text-zinc-500'}>
          {row.basis === 0 ? '0 (Z)' : '1 (X)'}
        </span>
      ),
    },
    {
      key: 'measured',
      header: 'Measured Bit',
      render: (row) => (
        <span className={`font-bold ${colors.step.bob.accent} ${colors.step.bob.glow} px-2 py-0.5 rounded bg-white border border-zinc-300`}>
          {row.measuredBit}
        </span>
      ),
    },
  ];

  return (
    <QuantumTable
      rows={rows}
      columns={columns}
      caption="Bob's Measurement"
      totalCount={rows.length}
      borderClass={colors.step.bob.border}
      headerBgClass={colors.step.bob.headerBg}
      visibleColumns={visibleColumns}
    />
  );
};
