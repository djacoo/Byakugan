# CSS — Working Standards

## Mindset
CSS is declarative and cascading. Work with the cascade — do not fight it with specificity hacks, `!important` overrides, and inline styles. A maintainable stylesheet has a clear structure, uses design tokens consistently, and grows predictably. Every visual property that is not derived from a token is a future maintenance problem.

## Before Writing Code
- Identify the styling methodology in use: BEM, CSS Modules, utility-first (Tailwind), or CSS-in-JS. Match it exactly.
- Check the existing design token system (custom properties, Tailwind config, or theme file) before hardcoding any value.
- Confirm the responsive strategy: mobile-first with `min-width` is the default. Understand the breakpoints.
- Check whether a component already exists that can be extended rather than writing new styles from scratch.
- Understand where the styles live in the project (co-located, global, modules) and follow that structure.

## How to Approach Any Task
1. Identify what already exists in the design token system that applies to this task.
2. Write the structural (layout) CSS first, then typographic, then visual (color, shadow, border).
3. Test on the defined breakpoints, not just the current viewport.
4. Check in a browser with forced dark mode if the project supports it.
5. Run Stylelint before considering the work done.

## Code Standards
- Use CSS custom properties for all design decisions: colors, spacing, typography, radii, shadows.
- Use `rem` for font sizes. Use `rem` or `%` for layout spacing. Use `px` only for borders and shadows.
- Use logical properties (`margin-inline`, `padding-block`) for internationalization support.
- Use `clamp()` for fluid typography and spacing values — avoid breakpoint-specific font-size overrides.
- Use `gap` for spacing between flex/grid items — not `margin` on children.
- Use `@layer` to organize the cascade: reset → tokens → base → components → utilities.
- Write media queries mobile-first (`min-width`). Group media queries with the component they belong to.
- Run Stylelint with `stylelint-config-standard` in CI.

## Hard Rules
- Never use `!important` except in utility override classes, and document why.
- Never hardcode color values outside the design token definition file.
- Never use `z-index` without a comment and a corresponding entry in the project's z-index scale.
- Never use `outline: none` or `outline: 0` without providing a visible alternative focus indicator.
- Never use `float` for layout (legacy only). Use Flexbox or Grid.
- Never nest selectors more than 3 levels deep.
- Never write styles that depend on the order of HTML elements unless truly unavoidable.
- Never set `overflow: hidden` without understanding and documenting what it clips.

## Accessibility Standards (Non-Negotiable)
- Color contrast: 4.5:1 for normal text, 3:1 for large text (WCAG AA minimum).
- Focus indicators must be visible on all interactive elements.
- Color alone must never convey information — use icons, text, or other visual cues too.
- `prefers-reduced-motion` media query must disable or reduce animations.
- `prefers-color-scheme` must be respected if the project supports dark mode.

## Definition of Done
- [ ] Stylelint passes with zero issues.
- [ ] No hardcoded color values outside the token file.
- [ ] No `!important` without documentation.
- [ ] No `z-index` without a scale entry and comment.
- [ ] Focus styles visible and not overridden without replacement.
- [ ] Responsive behavior verified at all defined breakpoints.
- [ ] Color contrast verified with a contrast checker.
- [ ] Dark mode tested if the project supports it.
- [ ] `prefers-reduced-motion` respected for animations.
