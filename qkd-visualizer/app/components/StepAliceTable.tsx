'use client';

import React from 'react';
import { QuantumTable, ColumnDef } from './QuantumTable';
import { colors } from '../constants/design-tokens';
import { InitializeConnectionResponse } from '../types/initialize_request';

export const getAliceGate = (bit: number, basis: number) => {
  if (bit === 0 && basis === 0) return '—';
  if (bit === 1 && basis === 0) return 'X';
  if (bit === 0 && basis === 1) return 'H';
  if (bit === 1 && basis === 1) return 'X+H';
  return '—';
};

export const getQubitState = (bit: number, basis: number) => {
  if (bit === 0 && basis === 0) return '|0⟩';
  if (bit === 1 && basis === 0) return '|1⟩';
  if (bit === 0 && basis === 1) return '|+⟩';
  if (bit === 1 && basis === 1) return '|−⟩';
  return '|0⟩';
};

interface StepAliceTableProps {
  result: InitializeConnectionResponse;
  visibleColumns: number;
}

export const StepAliceTable: React.FC<StepAliceTableProps> = ({ result, visibleColumns }) => {
  const rows = result.initial_alice_bits.map((bit, idx) => ({
    idx,
    bit,
    basis: result.initial_alice_bases[idx],
  }));

  const columns: ColumnDef<typeof rows[0]>[] = [
    {
      key: 'idx',
      header: '#',
      render: (row) => <span className="text-zinc-500">#{row.idx}</span>,
    },
    {
      key: 'bit',
      header: 'Initialize Bit',
      render: (row) => (
        <span className="font-bold text-black">{row.bit}</span>
      ),
    },
    {
      key: 'basis',
      header: 'Initialize Basis',
      render: (row) => (
        <span className={row.basis === 0 ? 'text-zinc-800' : 'text-zinc-500'}>
          {row.basis === 0 ? '0 (Z)' : '1 (X)'}
        </span>
      ),
    },
    {
      key: 'gate',
      header: 'Encode Gate',
      render: (row) => {
        const gate = getAliceGate(row.bit, row.basis);
        return (
          <span className="px-2 py-0.5 rounded bg-zinc-100 text-zinc-700 text-[10px] font-mono border border-zinc-200">
            {gate}
          </span>
        );
      },
    },
    {
      key: 'state',
      header: 'Qubit State',
      render: (row) => {
        const state = getQubitState(row.bit, row.basis);
        return (
          <span className={`font-bold ${colors.step.alice.accent} ${colors.step.alice.glow} px-2 py-0.5 rounded bg-white border border-zinc-300`}>
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
      caption="Alice's Qubit Preparation"
      totalCount={rows.length}
      borderClass={colors.step.alice.border}
      headerBgClass={colors.step.alice.headerBg}
      visibleColumns={visibleColumns}
    />
  );
};
