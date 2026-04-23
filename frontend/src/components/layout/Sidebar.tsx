import Link from 'next/link';

export function Sidebar() {
  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col p-4 space-y-4 shrink-0">
      <div className="font-semibold text-lg text-foreground px-2">Navigation</div>
      <nav className="flex flex-col space-y-2">
        <Link
          href="/"
          className="text-muted-foreground hover:text-foreground hover:bg-muted px-2 py-1.5 rounded-md transition-colors"
        >
          Dashboard
        </Link>
        <Link
          href="/settings"
          className="text-muted-foreground hover:text-foreground hover:bg-muted px-2 py-1.5 rounded-md transition-colors"
        >
          Settings
        </Link>
      </nav>
    </aside>
  );
}
