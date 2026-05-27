1.  **Fix Settings Page Layout**:
    *   Open `frontend/src/app/settings/page.tsx`.
    *   Update the root `div` from `<div className="max-w-5xl mx-auto space-y-6">` to `<div className="w-full min-h-screen flex flex-col p-4 md:p-8 ml-0 space-y-6">` as requested ("w-full min-h-screen flex flex-col p-4 md:p-8 ml-0").
    *   Update `<Tabs className="w-full">` to ensure it spans the full width.
    *   Update `<TabsContent>` wrappers (inside the `.map`) from their current layout to `<TabsContent key={cat} value={cat} className="w-full grid grid-cols-1 gap-6 pt-4">` to ensure they expand cleanly.
2.  **Verify UI**:
    *   Use Playwright to take a screenshot and confirm the layout stretches properly.
3.  **Pre-Commit & Submit**:
    *   Run tests, build, and submit.
