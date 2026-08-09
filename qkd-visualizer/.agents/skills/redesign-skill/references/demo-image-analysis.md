# Analyzing a Demo Image / Screenshot / Figma Export

When the user provides a demo image to follow, treat it as **inspiration and reference**, not a pixel-perfect spec to copy verbatim — especially if it conflicts with the existing app's established design language.

## What to extract from the demo image

- **Layout structure**: header/nav placement, content grid (columns, card layout vs. list), sidebar presence, footer.
- **Color palette**: primary/accent colors, background tones, text contrast levels. Note actual approximate hex values where discernible.
- **Typography**: heading weight/scale, body text size, any distinctive font pairing.
- **Spacing rhythm**: tight vs. airy, consistent gutter sizes, card padding.
- **Component shapes**: border-radius style (sharp vs. rounded vs. pill), shadow depth/style, button shapes.
- **Distinctive details**: anything that gives the demo its character — gradients, iconography style, dividers, empty states.

## Decide: adopt vs. adapt

For each element extracted above, classify it:

- **Adopt as-is** — elements that don't conflict with anything already established in the app (e.g. a new page's layout structure, since there's no existing precedent for that specific page).
- **Adapt to fit existing app** — elements that clash with already-established conventions elsewhere in the app (e.g. demo uses sharp corners but the rest of the app uses `rounded-2xl` everywhere; demo uses a different accent color than the app's existing primary color). In these cases, keep the *spirit* of the demo (e.g. "more spacious card layout") but translate it into the app's existing tokens rather than importing a second, conflicting style system.

Always state this classification explicitly in the implementation plan (Step 2 of the main workflow) so the user can correct you if their priority is actually to match the demo exactly, e.g.: "the demo uses a purple accent — I'll adapt this to your existing primary blue token rather than introduce a second brand color, unless you'd prefer to actually shift the whole app's accent color."

## When there's no existing app precedent yet (greenfield / first page)

If this is the very first styled page in the project, the demo image effectively *becomes* the seed for the new design-tokens file — extract its palette/spacing/radius into `constants/design-tokens.ts` (see `references/design-tokens.md`) so every subsequent page inherits from it, rather than re-eyeballing the demo image every time a new page is built.