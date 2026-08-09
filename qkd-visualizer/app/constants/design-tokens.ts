export const colors = {
  bg: {
    dark: '#ffffff', // changed to white
    card: 'rgba(255, 255, 255, 0.9)', 
    cardHover: 'rgba(250, 250, 250, 0.95)',
    input: 'rgba(244, 244, 245, 0.9)',
  },
  border: {
    subtle: 'rgba(0, 0, 0, 0.1)',
    glow: 'rgba(0, 0, 0, 0.2)',
    alert: 'rgba(0, 0, 0, 0.3)',
  },
  quantum: {
    cyan: '#000000',
    cyanGlow: '#000000',
    purple: '#3f3f46',
    indigo: '#52525b',
    emerald: '#000000',
    rose: '#71717a',
    amber: '#3f3f46',
  },
  text: {
    primary: '#000000',
    secondary: '#3f3f46',
    muted: '#71717a',
    accentCyan: '#000000',
    accentPurple: '#18181b',
  },
  step: {
    alice: {
      border: 'border-zinc-300',
      headerBg: 'bg-zinc-100',
      headerText: 'text-black',
      accent: 'text-black',
      badge: 'bg-white text-black border border-zinc-300',
      glow: 'shadow-[0_2px_10px_rgba(0,0,0,0.05)]',
    },
    eve: {
      border: 'border-zinc-400 border-dashed',
      headerBg: 'bg-zinc-200',
      headerText: 'text-zinc-900',
      accent: 'text-zinc-900',
      badge: 'bg-zinc-100 text-zinc-900 border border-zinc-400',
      glow: 'shadow-[0_2px_10px_rgba(0,0,0,0.1)]',
    },
    bob: {
      border: 'border-zinc-300',
      headerBg: 'bg-zinc-100',
      headerText: 'text-zinc-900',
      accent: 'text-zinc-900',
      badge: 'bg-white text-zinc-900 border border-zinc-300',
      glow: 'shadow-[0_2px_10px_rgba(0,0,0,0.05)]',
    },
    match: {
      badge: 'bg-black text-white border border-black',
    },
    mismatch: {
      badge: 'bg-zinc-100 text-zinc-600 border border-zinc-300',
    },
  },
} as const;

export const gradients = {
  heroText: 'from-black via-zinc-700 to-zinc-500',
  quantumCard: 'bg-gradient-to-br from-white via-zinc-50 to-zinc-100',
  cyanButton: 'bg-gradient-to-r from-black via-zinc-900 to-zinc-800 hover:from-zinc-900 hover:to-zinc-700',
  purpleButton: 'bg-gradient-to-r from-zinc-200 via-zinc-100 to-white text-black',
  dangerBadge: 'bg-gradient-to-r from-white to-zinc-100 border-zinc-300 text-zinc-800',
  safeBadge: 'bg-gradient-to-r from-black to-zinc-800 border-black text-white',
} as const;

export const shadow = {
  cyanGlow: 'shadow-[0_5px_20px_rgba(0,0,0,0.08)]',
  purpleGlow: 'shadow-[0_5px_20px_rgba(0,0,0,0.05)]',
  roseGlow: 'shadow-[0_5px_20px_rgba(0,0,0,0.1)]',
} as const;
