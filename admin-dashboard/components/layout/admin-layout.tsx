"use client"

export function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-64 border-r bg-muted/40">
          <div className="flex h-14 items-center border-b px-4">
            <h1 className="text-lg font-semibold">Admin Dashboard</h1>
          </div>
          <nav className="space-y-2 p-4">
            <a href="/" className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent">
              <span>Dashboard</span>
            </a>
            <a href="/documents" className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent">
              <span>Documents</span>
            </a>
            <a href="/websites" className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent">
              <span>Websites</span>
            </a>
            <a href="/collections" className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent">
              <span>Collections</span>
            </a>
          </nav>
        </div>
        
        {/* Main content */}
        <div className="flex-1">
          <header className="border-b">
            <div className="flex h-14 items-center px-6">
              <h2 className="text-lg font-semibold">GovStack Admin</h2>
            </div>
          </header>
          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
