# Design tokens

`static/css/variables.css` is the source of truth for the editorial noir
design. Dark is the default; `data-theme="light"` overrides the page colours.
The header, hero, project hero and assistant remain dark in both themes and use
the `stage` tokens.

## Type and spacing

- Use `--font-display` for display headings, `--font-body` for content and
  `--font-mono` for labels and controls.
- Use `--text-2xs` (12px at the default root size) or larger for labels;
  body copy uses `--text-base` and `--leading-body`.
- Use `--space-1` through `--space-10` rather than arbitrary gaps; use
  `--shell-pad` and `--section-pad` for responsive gutters and sections.

## Colours and states

- Use primary, secondary and muted text on `--color-bg` or `--color-surface`;
  use the `on-stage` variants on dark stage surfaces.
- Use `--color-accent` for text and outlines on page surfaces;
  `--color-accent-fill` and `--color-on-accent` belong together on buttons.
  Use the stage accent on dark stage surfaces, even in light mode.
- Preserve visible `:focus-visible` outlines and non-colour cues on links;
  filled red controls use a contrasting outline. Keep touch targets at least
  44px where practical.
- Use `--dur-fast`, `--dur-base`, `--dur-slow` and `--ease-out` for motion,
  and preserve the reduced-motion rules in `motion.css`.

The semantic foreground/background combinations in use are checked in
`portfolio/test_design_tokens.py`: normal text requires 4.5:1 and meaningful
non-text indicators require 3:1. Add a pair there when introducing a new
combination. Decorative borders, shadows and translucent overlays are not
text pairs; verify any new composited combination in its actual context.
