'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ColumnDef<T> {
  key: string;
  header: string;
  headerClass?: string;
  render: (row: T, index: number) => React.ReactNode;
  cellClass?: string;
}

interface QuantumTableProps<T> {
  rows: T[];
  columns: ColumnDef<T>[];
  caption: string;
  totalCount: number;
  borderClass: string;
  headerBgClass: string;
  visibleColumns: number; // how many columns are currently revealed
  headCount?: number; // default 5
  tailCount?: number; // default 5
}

export function QuantumTable<T>({
  rows,
  columns,
  caption,
  totalCount,
  borderClass,
  headerBgClass,
  visibleColumns,
  headCount = 5,
  tailCount = 5,
}: QuantumTableProps<T>) {
  const showEllipsis = totalCount > headCount + tailCount;
  const headRows = rows.slice(0, headCount);
  const tailRows = showEllipsis ? rows.slice(rows.length - tailCount) : [];
  const displayedCols = columns.slice(0, visibleColumns);

  return (
    <div className={`rounded-2xl border ${borderClass} overflow-hidden`}>
      {/* Caption / total count */}
      <div className={`${headerBgClass} px-4 py-2.5 flex items-center justify-between border-b ${borderClass}`}>
        <span className="text-xs font-semibold text-zinc-600 uppercase tracking-wider">{caption}</span>
        <span className="text-xs font-mono text-zinc-600 bg-white px-2.5 py-1 rounded-full border border-zinc-300">
          {totalCount} rows total
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-zinc-100 sticky top-0">
            <tr>
              {columns.map((col, ci) => (
                <AnimatePresence key={col.key}>
                  {ci < visibleColumns && (
                    <motion.th
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.35, delay: ci * 0.08 }}
                      className={`px-4 py-3 font-semibold text-zinc-700 whitespace-nowrap border-b ${borderClass} ${col.headerClass ?? ''}`}
                    >
                      {col.header}
                    </motion.th>
                  )}
                </AnimatePresence>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {/* Head rows */}
            {headRows.map((row, ri) => (
              <motion.tr
                key={`head-${ri}`}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: ri * 0.04 }}
                className="hover:bg-zinc-50 transition-colors bg-white"
              >
                {displayedCols.map((col, ci) => (
                  <motion.td
                    key={col.key}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.25, delay: ri * 0.04 + ci * 0.06 }}
                    className={`px-4 py-2.5 ${col.cellClass ?? 'text-zinc-800'}`}
                  >
                    {col.render(row, ri)}
                  </motion.td>
                ))}
              </motion.tr>
            ))}

            {/* Ellipsis row */}
            {showEllipsis && (
              <tr className="bg-zinc-50/50">
                <td
                  colSpan={displayedCols.length}
                  className="px-4 py-2 text-center text-zinc-500"
                >
                  <div className="flex flex-col items-center gap-0.5 py-1">
                    <span className="text-zinc-400">·</span>
                    <span className="text-zinc-400">·</span>
                    <span className="text-zinc-400">·</span>
                    <span className="text-[10px] text-zinc-500 mt-1">
                      {totalCount - headCount - tailCount} more rows hidden
                    </span>
                  </div>
                </td>
              </tr>
            )}

            {/* Tail rows */}
            {tailRows.map((row, ri) => {
              const actualIdx = totalCount - tailCount + ri;
              return (
                <motion.tr
                  key={`tail-${ri}`}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: (headCount + ri) * 0.04 }}
                  className="hover:bg-zinc-50 transition-colors bg-white"
                >
                  {displayedCols.map((col, ci) => (
                    <motion.td
                      key={col.key}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.25, delay: (headCount + ri) * 0.04 + ci * 0.06 }}
                      className={`px-4 py-2.5 ${col.cellClass ?? 'text-zinc-800'}`}
                    >
                      {col.render(row, actualIdx)}
                    </motion.td>
                  ))}
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
