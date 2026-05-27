1.  **Refactor Dashboard (`frontend/src/app/page.tsx`)**:
    *   Change the layout to a strict 4-quadrant grid using non-collapsible containers (e.g., `grid-cols-2 grid-rows-2`).
    *   **Quadrant 1 (System Integrity Pool)**: Implement mock data/state for total vs. scanned storage capacity, active throughput (items/sec), and ZFS snapshot cache safety status indicator.
    *   **Quadrant 2 (Deep Core Audit / Telemetry)**: Implement counters for Bit-Rot Alerts, Truncated Media Assets, and Corrupted EXIF/Headers.
    *   **Quadrant 3 (Remediation Deltas)**: Implement cumulative counters for ZFS Snapshot Restores, Cloud API Fetches, and Generative AI Infills.
    *   **Quadrant 4 (Retention Queue Clock)**: Implement a warning timeline list tracking items nearing pruning deadlines with countdowns.
2.  **Refactor File Browser (`frontend/src/app/browser/page.tsx`)**:
    *   Redesign as a responsive dual-pane layout.
    *   **Left Pane**: Expandable directory tree explicitly listing `/media`, `/watch`, and `/quarantine`.
    *   **Task Progress Hub**: Add a progress widget at the *bottom of the left pane* showing active scanning progress and current filename.
    *   **Right Pane (Asset Grid)**: Display thumbnails/cards for files in the selected directory.
        *   Add color-coded integrity indicators (Green/Yellow/Red).
        *   Implement a Shadcn custom context menu on right-click for files with actions: Scan, Delete, Rename, Copy Path, Move. Hook these up to existing backend API routes if possible, or stub them out with toasts.
3.  **Refactor Triage (`frontend/src/app/triage/page.tsx`)**:
    *   Add a global toggle for Gallery (thumbnail) vs. List (high-density, small icons) views.
    *   Implement a full-screen mobile-responsive overlay modal/popup for the **Side-by-Side Review Flyout**.
    *   **Review Flyout Contents**:
        *   Action buttons: Request Snapshot Restore, Pull Cloud Copy.
        *   AI sub-menu: Toggle between Cloud AI Engine and Local Compute Worker Node.
        *   AI Prompt modifier: Textarea for custom instructions.
        *   **Manual Overwrite Drop-Zone**: A functional drag-and-drop area for uploading a corrected file, mapping to `POST /triage/{id}/upload-replacement`.
        *   **Require Human Review Gateway**: A high-visibility warning tracking "Veto Pending" (infinite TTL) vs standard TTL (30d/90d).
4.  **Backend Enhancements (if necessary)**:
    *   Review `backend/app/api/triage.py` and `backend/app/api/routers.py` to ensure the required endpoints for Triage (AI overrides, replacements) exist. Add them if missing.
5.  **Pre-commit & Final Polish**:
    *   Verify all layouts use Tailwind grids and do not break flow.
    *   Enforce robust TypeScript types for all new mock data and states.
    *   Run `pre_commit_instructions` tool to verify checks pass.
    *   Submit changes.
