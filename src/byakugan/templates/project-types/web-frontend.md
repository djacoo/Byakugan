# Web Frontend — Working Standards

## What This Project Type Demands
The frontend is what users experience directly. Performance, accessibility, and reliability are product requirements — not engineering niceties. The network is unreliable. The browser is unpredictable. Users run ad-blockers, screen readers, keyboard-only navigation, and slow connections. Build for all of them.

## Before Starting Any Feature
- Establish what state this feature requires: local UI state, shared client state, or server state? Use the right tool for each.
- Define loading, error, and empty states before writing any rendering logic.
- Identify all data sources: which API endpoints are called, what the response shapes are, what can fail.
- Determine accessibility requirements: keyboard navigation flow, ARIA roles, focus management for modals/dialogs.
- Identify if this feature affects Core Web Vitals (layout shift, largest paint, interaction latency).

## Architecture Standards
- Strict separation of concerns: data-fetching components are separate from presentational components.
- State lives at the right level: local state in the component, shared UI state in a store/context, server state via a data-fetching library (React Query, SWR, Apollo).
- Unidirectional data flow: state flows down, events flow up. No two-way binding outside form inputs.
- Co-locate related files: component, test, story, and styles in one directory.
- Lazy-load routes and large components. Split at route boundaries.

## How to Approach Any Task
1. Read the existing component library and design system before creating anything new.
2. Write semantic HTML first. Add CSS for visual presentation. Add JavaScript for interactivity. In that order.
3. Build the component with all states: loading skeleton, error message, empty state, and the data state.
4. Write component tests using `@testing-library` before the component is considered done.
5. Check in a screen reader (VoiceOver/NVDA) and via keyboard-only navigation before marking accessibility as done.

## Non-Negotiable Rules
- All images have `alt` text. Decorative images use `alt=""`.
- All form inputs have associated `<label>` elements. No placeholder-only labels.
- Color alone never conveys information — use text, icons, or patterns alongside color.
- Interactive elements are reachable and operable by keyboard.
- Focus indicators are visible and never removed without a replacement.
- No `dangerouslySetInnerHTML` / `v-html` / `innerHTML` on user-provided content without sanitization.
- API errors shown to the user. Silent failures are not acceptable.
- Lists with dynamic keys use stable IDs, never array indices.

## Performance Standards
- Core Web Vitals targets: LCP < 2.5s, INP < 200ms, CLS < 0.1.
- No layout shift from async-loaded content — set explicit dimensions for images and dynamic content containers.
- Images use `loading="lazy"` below the fold. Hero images preloaded with `<link rel="preload">`.
- JS bundles split at route boundaries. No loading all application code upfront.
- Lists with 50+ items use virtualization.
- Run Lighthouse in CI and fail on regressions.

## Testing Standards
- Unit tests for utility functions and custom hooks.
- Component tests with `@testing-library` — test what users see and do, not implementation details.
- Use `getByRole`, `getByLabelText`, `getByText` — avoid `getByTestId` for user-facing assertions.
- Accessibility tests with `jest-axe` in component tests.
- E2E tests with Playwright for 5–10 critical user journeys only.

## Definition of Done
- [ ] All defined states implemented: loading, error, empty, data.
- [ ] Keyboard navigation tested and working.
- [ ] Screen reader verification done (VoiceOver or NVDA).
- [ ] Color contrast meets WCAG AA (4.5:1 for normal text).
- [ ] No `dangerouslySetInnerHTML` on user-provided content.
- [ ] `@testing-library` component tests written and passing.
- [ ] No layout shift from the new feature (CLS impact checked).
- [ ] Errors from API calls are shown to the user.
- [ ] Lighthouse score not regressed.
