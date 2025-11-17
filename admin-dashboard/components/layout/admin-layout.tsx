"use client"

import { 
  BuildingOfficeIcon,
  HomeIcon,
  DocumentTextIcon,
  GlobeAltIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const navigation = [
    {
      name: 'Agencies',
      href: '/agencies',
      icon: BuildingOfficeIcon,
    },
    {
      name: 'Dashboard',
      href: '/',
      icon: HomeIcon,
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: DocumentTextIcon,
    },
    {
      name: 'Websites',
      href: '/websites',
      icon: GlobeAltIcon,
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-64 border-r bg-muted/40">
          <div className="flex h-14 items-center border-b px-4">
            <h1 className="text-lg font-semibold">Admin Dashboard</h1>
          </div>
          <nav className="space-y-2 p-4">
            {navigation.map((item) => (
              <a key={item.name} href={item.href} className="flex items-center space-x-2 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent">
                <span>{item.name}</span>
              </a>
            ))}
          </nav>
        </div>
        
        {/* Main content */}
        <div className="flex-1">
          <header className="border-b">
            <div className="flex h-14 items-center px-6">
              <h2 className="text-lg font-semibold">GovBot Admin</h2>
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
