# Kintsugi-DAM: UI/UX Design System & AI Instructions

## 1. Core Philosophy & Aesthetic
* **The Vibe:** Modern Web3, Command-Center, Minimalist. The application should feel like a high-performance, precision instrument.
* **Mobile-First Absolute Rule:** The UI must be fully functional and aesthetically pleasing on a mobile screen. 
    * *AI Agent Instruction:* ALWAYS design the mobile layout first using base Tailwind classes (e.g., `flex-col`, `w-full`). Only apply desktop layouts using responsive prefixes (e.g., `md:flex-row`, `md:grid-cols-3`). NEVER use fixed pixel widths for layout containers; use percentages or viewport units.
* **Card-Based UI:** All grouped information, settings, and media items must be contained within distinct, subtly bordered Cards (`shadcn/ui` Card component).

## 2. Dynamic Theming & Color Palette
The application utilizes a dynamic theming system powered by CSS variables and standard Next-Themes integration.

### The 4 Core Themes:
1. **OLED Dark (Default):** * Background: True Black (`#000000`).
   * Cards/Surfaces: Extremely dark gray/blue-tint (`#09090b` or `#111827`).
   * Text: Pure White for headings, light gray (`text-muted-foreground`) for secondary text.
2. **Light Mode:** * Background: Pure White (`#ffffff`).
   * Cards/Surfaces: Off-white/light gray (`#f4f4f5`).
   * Text: Near Black (`#09090b`).
3. **Accent Colors (The "Echo Sync" Vibe):** * Primary Accent: A punchy, neon Mint Green (e.g., `emerald-500` or `#10b981`) for "Active" states, positive actions, and primary buttons.
   * Destructive Accent: A sharp Red (`red-500`) for "Quarantine" or delete warnings.
   * *AI Agent Instruction:* Utilize the `primary` CSS variables defined in the `globals.css` via shadcn. Do not hardcode hex colors in the Tailwind classes.

## 3. Typography
* **Font:** `Inter`, `Geist`, or system sans-serif.
* **Hierarchy:** * Headings must be bold, tight-tracked, and clean.
    * Subtext and helper text must be distinctly smaller and muted to prevent visual clutter in settings panels.
    * Monospace font (e.g., `JetBrains Mono` or `Fira Code`) must be used for all file paths, hashes (SHA-256), and CLI output logs.

## 4. Layout Constraints & Component Rules
* **Touch Targets:** All interactive elements (buttons, switches, dropdowns) must have a minimum height/width of `44px` on mobile screens to ensure tap accessibility.
* **The Triage Gallery:** * Mobile: Single column (`grid-cols-1`). Image thumbnail on top, path/hash data below.
    * Desktop: Masonry or strict grid (`md:grid-cols-3` or `4`).
* **Settings & Plugin UI:** Use a stacked list of cards. Each setting should feature a label and helper text on the left, with the toggle/input on the far right (similar to iOS settings).

## 5. UI Component Library (`shadcn/ui`)
* Do not write custom CSS for base components. 
* Strictly utilize the following `shadcn/ui` components for consistency:
    * `Card` (Header, Title, Content, Footer) for all layouts.
    * `Switch` for boolean plugin configurations.
    * `Badge` (with default, secondary, and destructive variants) for file states (e.g., `[CORRUPTED]`, `[CLEAN]`).
    * `Progress` or `Skeleton` loaders for async file scanning feedback.
    * `Dialog` (Modals) for all destructive/remediation confirmations (e.g., "Are you sure you want to Auto-Restore this file?").