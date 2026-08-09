# Design Tokens — Structure & Wiring

Goal: every color (and ideally spacing/radius/font-size scale) lives in **one constants file**, never scattered as raw hex codes or ad-hoc Tailwind color classes across components. Components reference tokens, tokens reference values.

## Where the file lives

Place it under a `constants/` folder, e.g.:

```
src/constants/design-tokens.ts   (or theme.ts / colors.ts)
```

If the project already has a `constants/` folder with a different file for this, extend that file instead of creating a second one.

## Approach A — CSS variables + Tailwind config (preferred for most projects)

This is the more idiomatic Tailwind approach and plays well with dark mode.

**1. `src/constants/design-tokens.ts`** — the single source of truth, exported as plain JS values (useful for JS-side usage: charts, inline SVGs, dynamic styles that truly can't be Tailwind classes):

```ts
// src/constants/design-tokens.ts
export const colors = {
  primary: {
    DEFAULT: '#2563eb',
    hover: '#1d4ed8',
    subtle: '#eff6ff',
  },
  neutral: {
    bg: '#ffffff',
    surface: '#f8fafc',
    border: '#e2e8f0',
    textPrimary: '#0f172a',
    textSecondary: '#64748b',
  },
  accent: {
    success: '#16a34a',
    warning: '#d97706',
    danger: '#dc2626',
  },
} as const;

export const radii = {
  sm: '0.375rem',
  md: '0.5rem',
  lg: '1rem',
  full: '9999px',
} as const;

export const spacing = {
  section: '4rem',
  card: '1.5rem',
} as const;
```

**2. Mirror the same values as CSS variables** (e.g. in the single root layout file's `:root`, NOT a sprawling global stylesheet — this is just variable declarations, not styling rules):

```css
:root {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-neutral-bg: #ffffff;
  --color-neutral-surface: #f8fafc;
  --color-neutral-border: #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;
}
```

**3. Map them in `tailwind.config.js`** so components use normal Tailwind utility classes:

```js
theme: {
  extend: {
    colors: {
      primary: {
        DEFAULT: 'var(--color-primary)',
        hover: 'var(--color-primary-hover)',
      },
      surface: 'var(--color-neutral-surface)',
      border: 'var(--color-neutral-border)',
    },
  },
}
```

**4. Components just use Tailwind classes normally** — `bg-primary`, `text-primary-hover`, `border-border` — never a raw hex or a random `bg-blue-500`. This keeps JSX clean while the actual values are 100% centralized in one file + one config.

## Approach B — Plain constants object (no CSS variables)

Simpler for smaller apps or when the stack doesn't use a `tailwind.config` theme extension (e.g. Tailwind v4 CSS-first config, or a quick prototype). Still centralize in `constants/design-tokens.ts`, and reference it via a `cn()` helper or by composing className strings from the constants:

```ts
// src/constants/design-tokens.ts
export const tw = {
  bg: {
    primary: 'bg-blue-600',
    primaryHover: 'hover:bg-blue-700',
    surface: 'bg-slate-50',
  },
  text: {
    primary: 'text-slate-900',
    secondary: 'text-slate-500',
  },
  border: 'border-slate-200',
  radius: {
    card: 'rounded-2xl',
    button: 'rounded-lg',
  },
} as const;
```

```tsx
import { tw } from '@/constants/design-tokens';

<button className={`${tw.bg.primary} ${tw.bg.primaryHover} ${tw.radius.button} px-4 py-2 text-white`}>
  Save
</button>
```

Use Approach B when the project has no existing CSS-variable convention and you want minimal setup. Use Approach A when the project already has (or should have) proper dark-mode/theming support, since CSS variables switch cleanly per theme.

## Rules regardless of approach

- Never write `bg-[#2563eb]` or similar raw hex arbitrary values in a component — that's a hardcoded color hiding in disguise. If a one-off value is genuinely needed, add it to the tokens file first, then reference the token.
- Never create a second/competing tokens file — search for an existing one first (`grep -ri "tokens\|theme\|colors" src/constants` or similar) and extend it.
- Keep the tokens file itself free of component logic — it's data only, no JSX, no functions beyond maybe simple getters.
- If the app has both light and dark mode, express that in the tokens file/CSS variables, not with scattered `dark:` overrides re-declaring colors inline everywhere.