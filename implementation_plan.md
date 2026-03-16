# Navbar Redesign Plan

## Goal Description
Redesign the current `top-nav.tsx` to a new style since the user requested trying another different style. We will implement a "Split Floating" dashboard navigation style.

## Proposed Changes

### `top-nav.tsx` modifications
We will modify the TopNav component to feature a detached, split layout where the logo, navigation links, and right-hand actions sit in their own individual floating "pills" at the top of the screen.

- The header container will be `fixed top-4 w-full px-6 flex justify-between items-center pointer-events-none`.
- Logo pill: Left aligned, `bg-[#0A0A0B]/80 backdrop-blur-md border border-white/10 rounded-full px-4 py-2 pointer-events-auto`.
- Center Nav pill: Centered horizontally, containing the links. Active links will have a glowing background highlight rather than an underline. `bg-[#0A0A0B]/80 backdrop-blur-md border border-white/10 rounded-full px-2 py-1.5 pointer-events-auto`.
- Right Actions pill: Right aligned, containing the score and docs link. `bg-[#0A0A0B]/80 backdrop-blur-md border border-white/10 rounded-full px-4 py-2 pointer-events-auto`.

## Verification Plan
### Automated Tests
- Check if Vite dev server compiles without errors.

### Manual Verification
- Review the new navbar visually in the browser to ensure the three separate floating pills look cohesive, the hover and active animations work smoothly, and the floating elements do not obstruct the content in an annoying way.
