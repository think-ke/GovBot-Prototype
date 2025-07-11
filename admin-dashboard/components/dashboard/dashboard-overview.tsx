"use client"

export function DashboardOverview() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard Overview</h1>
        <p className="text-muted-foreground">Welcome to the GovStack Admin Dashboard</p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Webpages</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Collections</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Active Crawls</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">No recent activity</p>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">System Status</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">API Status</span>
              <span className="text-sm text-green-600">Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Database</span>
              <span className="text-sm text-green-600">Connected</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Storage</span>
              <span className="text-sm text-green-600">Available</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
