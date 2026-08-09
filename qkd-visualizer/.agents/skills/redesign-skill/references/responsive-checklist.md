# Responsive Design — Breakpoints & Checklist

Every redesigned page/component must work cleanly across three target sizes. Build mobile-first: unprefixed classes = phone baseline, then add `md:` and `lg:`/`xl:` layers on top.

## Target breakpoints

| Target | Approx width | Tailwind prefix to start using |
|---|---|---|
| Phone | ~375–428px | (base, no prefix) |
| iPad / tablet | ~768–1024px | `md:` (768px) and/or `lg:` if layout needs the extra room at 1024px |
| Desktop | ~1280px+ | `lg:` (1024px) and `xl:` (1280px) |

Tailwind's default breakpoints: `sm:640px`, `md:768px`, `lg:1024px`, `xl:1280px`, `2xl:1536px`. For this skill, treat `md:` as "iPad portrait+" and `lg:`/`xl:` as "desktop."

## Mobile-first patterns to apply

- **Layout**: start single-column (`flex flex-col` / `grid grid-cols-1`), then expand: `md:grid-cols-2 lg:grid-cols-3`, or introduce a sidebar only from `lg:` (`lg:flex-row`, `lg:w-64`).
- **Navigation**: hamburger/drawer nav on phone and often still on iPad portrait; full horizontal nav from `lg:` (or `md:` if the design has few nav items).
- **Spacing**: tighter padding on phone (`p-4`), more breathing room on larger screens (`md:p-6 lg:p-8`).
- **Typography**: slightly smaller headings on phone (`text-2xl md:text-3xl lg:text-4xl`); keep body text roughly consistent (`text-base`) since readability shouldn't shrink much.
- **Touch targets**: buttons/inputs need real tap area on phone/iPad — minimum ~44px tall (`h-11` or `py-3`), don't rely only on desktop-style compact controls.
- **Images/media**: use `w-full h-auto` or aspect-ratio utilities (`aspect-video`, `aspect-square`) so media scales instead of overflowing.
- **Tables**: wide tables need a horizontal-scroll wrapper on phone (`overflow-x-auto`) or should collapse into cards on phone with `md:table` layout appearing at tablet+.
- **Modals/dialogs**: full-screen or near-full-screen on phone, centered fixed-width panel from `md:`/`lg:`.

## Pre-delivery checklist

Before presenting a redesigned screen as finished, verify:

- [ ] Renders without horizontal overflow at ~375px width.
- [ ] Renders sensibly at ~768–1024px (iPad) — not just a stretched phone layout, not a cramped desktop layout.
- [ ] Renders well at ~1280px+ desktop — content doesn't awkwardly hug one side or stretch into overly long line lengths (cap text containers with `max-w-*` where appropriate).
- [ ] Nav/menu has an explicit mobile pattern (drawer/hamburger) and an explicit larger-screen pattern, not just a squeezed version of one.
- [ ] Interactive elements (buttons, inputs, links in nav) meet a comfortable tap size on phone/iPad.
- [ ] Grids/columns actually change across breakpoints (verify at least one `md:` and one `lg:`/`xl:` grid/flex-direction change is present — a design with zero responsive prefixes is not done).
- [ ] Colors/spacing all reference the design-tokens constants file — no raw hex or stray Tailwind color utilities bypassing tokens.
- [ ] Visual rhythm (spacing scale, radius, shadows, type scale) matches other pages already in the app.