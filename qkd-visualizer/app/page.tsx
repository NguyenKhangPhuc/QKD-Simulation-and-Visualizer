'use client';

import React, { useState } from 'react';
import { HeroSection } from './components/HeroSection';
import { QkdVisualizerSection } from './components/QkdVisualizerSection';

export default function Home() {
  const [isEve, setIsEve] = useState<boolean>(false);

  return (
    <main className="min-h-screen bg-white text-zinc-900 selection:bg-zinc-800 selection:text-white">
      {/* Main Content */}
      <HeroSection />

      <QkdVisualizerSection
        isEve={isEve}
        setIsEve={setIsEve}
      />

      {/* Footer */}
      <footer className="border-t border-zinc-200 py-8 text-center text-xs text-zinc-500 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          BB84 Quantum Key Distribution Visualizer &bull; Powered by Qiskit &amp; FastAPI
        </div>
      </footer>
    </main>
  );
}
