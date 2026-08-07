---
name: redesign-skill
description: Use this skill whenever the user wants to redesign, restyle, refresh, or visually overhaul an existing app, website, page, or component — even if they just say "make this look better", "modernize this UI", "redesign this page", or share a design/screenshot/Figma image to follow. Always trigger this for any UI/visual redesign work, not just when the word "redesign" is used explicitly. Enforces Tailwind-only styling, a centralized color/design-token constants file (no global CSS), a mandatory implementation plan before coding, visual consistency with existing pages, optional demo-image analysis, and mandatory responsive support for phone, iPad/tablet, and desktop breakpoints.
---

# Redesign App

A workflow for redesigning UI while keeping the whole app visually consistent, using Tailwind only, centralized design tokens, and a mandatory plan-before-code process.

## Core rules (never break these)

1. **Tailwind only.** No global CSS files, no `<style>` blocks, no CSS-in-JS, no inline `style={{}}` for anything expressible in Tailwind. If a truly custom value is unavoidable (e.g. a very specific box-shadow), use Tailwind's arbitrary value syntax (`shadow-[0_4px_20px_rgba(0,0,0,0.08)]`) instead of writing raw CSS.
2. **No hardcoded colors in components.** Every color (backgrounds, text, borders, accents, gradients) must come from a constants file, never typed directly as a Tailwind class like `bg-blue-500` scattered across components. See "Design tokens" below.
3. **Always produce an implementation plan first**, and get the user's explicit go-ahead (or clear intent to proceed) before writing code. Never jump straight to code generation on a redesign request.
4. **Consistency with existing pages beats novelty.** If the app already has other redesigned/existing pages, study them first and match their patterns (spacing scale, component shapes, color usage, typography). A demo image, if provided, is inspiration to analyze and adapt — not a pixel-perfect spec to copy blindly. When demo image and existing app patterns conflict, prioritize existing app consistency and tell the user you're doing so.
5. **Always responsive.** Every redesigned screen must work at minimum three breakpoints: phone (~375px), iPad/tablet (~768–1024px), and desktop (~1280px+). Never ship a design that only targets one size.

## Workflow

### Step 1 — Gather context (do this before proposing anything)

- Find and read the existing codebase's current pages/components to learn the established patterns: spacing, border-radius, shadow style, typography scale, component library in use (shadcn/ui, headlessui, custom, etc.).
- Look for an existing design-tokens/constants file (see naming patterns in `references/design-tokens.md`). If one exists, use it as the source of truth and extend it rather than replacing it.
- If the user attached a demo image/screenshot/Figma export, analyze it: layout structure, color palette, spacing rhythm, typography, component shapes. Note what's inspiration vs. what conflicts with existing app conventions.
- If no prior pages exist yet (greenfield), this is the first design pass — establish the token file conventions from `references/design-tokens.md` now, since everything after will need to match it.

### Step 2 — Write the implementation plan

Present a short plan to the user before touching code. Always include:

- **Scope**: which pages/components are being redesigned.
- **Design tokens**: what's changing or being added in the constants file (colors, spacing scale, radii, font sizes) — list them concretely, not vaguely.
- **Layout approach per breakpoint**: how the layout adapts across phone / iPad / desktop (e.g. "single column on phone, 2-column grid from `md:`, sidebar appears from `lg:`").
- **Consistency notes**: what's being reused from existing pages vs. what's new, and why.
- **Demo image notes** (if applicable): what's being adopted from the demo vs. adapted to fit existing app conventions.

Wait for confirmation (or clear signal to proceed, e.g. "looks good, do it") before generating code. If the user gives a big open-ended ask ("redesign my whole app"), the plan should still cover all pages at a summary level, but implement incrementally page by page.

### Step 3 — Set up / update the design tokens constants file

Follow `references/design-tokens.md` for the exact file structure and Tailwind wiring (CSS variables + `tailwind.config` mapping, or a plain JS/TS constants object, depending on stack — that reference file covers both). Never let component files declare raw hex/rgb colors — they must import from this constants file.

### Step 4 — Implement components/pages

- Use only Tailwind utility classes, pulling colors/spacing from the token constants (via Tailwind config theme extension, or via a `cn()`/className helper referencing token constants — see reference file for patterns).
- Build mobile-first: base classes target phone, then layer `md:` for iPad/tablet and `lg:`/`xl:` for desktop.
- Reuse existing shared components where they exist rather than creating near-duplicates.
- Follow `references/responsive-checklist.md` to verify every screen before presenting it as done.

### Step 5 — Self-check before delivering

Run through `references/responsive-checklist.md` and confirm:
- No raw color values or global CSS crept in.
- Tokens file is the single source of truth for colors used.
- Phone/iPad/desktop all render sensibly (check for overflow, cramped touch targets, awkward line lengths).
- New pages visually rhyme with existing ones (spacing, radius, shadow, type scale).

## Reference files

- `references/design-tokens.md` — exact structure for the constants/tokens file, how to wire it into Tailwind (CSS variables approach and plain-object approach), and import patterns for components.
- `references/responsive-checklist.md` — breakpoint targets, mobile-first patterns, and a concrete checklist to run before calling a redesign done.
- `references/demo-image-analysis.md` — how to analyze a provided demo/screenshot and separate "adopt as-is" vs "adapt to fit existing app" decisions.