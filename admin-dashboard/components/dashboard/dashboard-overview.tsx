"use client"

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { DashboardStats } from '@/lib/types'

export function DashboardOverview() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [systemHealth, setSystemHealth] = useState<any>(null)
  const [recentDocuments, setRecentDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [
        dashboardStats,
        healthData,
        documents,
        collections
      ] = await Promise.all([
        apiClient.getDashboardStats().catch(() => null),
        apiClient.getSystemHealth().catch(() => null),
        apiClient.getDocuments({ limit: 5 }).catch(() => []),
        apiClient.getCollections().catch(() => [])
      ])

      // Calculate real stats from API data
      const realStats: DashboardStats = {
        total_documents: documents.length,
        total_webpages: 0, // Would need webpage count from API
        total_collections: collections.length,
        total_storage_size: documents.reduce((sum, doc) => sum + (doc.size || 0), 0),
        active_crawl_jobs: 0, // Would need crawl status from API
        recent_uploads: documents.filter(doc => {
          const uploadDate = new Date(doc.upload_date)
          const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
          return uploadDate > oneDayAgo
        }).length
      }

      setStats(realStats)
      setSystemHealth(healthData)
      setRecentDocuments(documents.slice(0, 5))
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Overview</h1>
          <p className="text-muted-foreground">Welcome to the GovStack Admin Dashboard</p>
        </div>
        <button 
          onClick={loadDashboardData}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
              <p className="text-2xl font-bold">{stats?.total_documents || 0}</p>
            </div>
          </div>
          {stats?.recent_uploads !== undefined && (
            <p className="text-xs text-muted-foreground mt-2">
              {stats.recent_uploads} uploaded today
            </p>
          )}
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Webpages</p>
              <p className="text-2xl font-bold">{stats?.total_webpages || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Collections</p>
              <p className="text-2xl font-bold">{stats?.total_collections || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Storage Used</p>
              <p className="text-2xl font-bold">
                {stats?.total_storage_size ? (stats.total_storage_size / 1024 / 1024).toFixed(1) : '0'} MB
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* System Health */}
      {systemHealth && (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-2">System Health</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Uptime</span>
                <span className="font-medium">{systemHealth.uptime_percentage}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Status</span>
                <span className={`text-sm font-medium ${
                  systemHealth.system_availability === 'healthy' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {systemHealth.system_availability}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Response Time</span>
                <span className="font-medium">{systemHealth.api_response_time_p50}ms</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-2">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Upload Documents
              </button>
              <button className="w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Start Web Crawl
              </button>
              <button className="w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Create Collection
              </button>
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-2">Navigation</h3>
            <div className="space-y-2">
              <a href="/documents" className="block w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Document Management
              </a>
              <a href="/collections" className="block w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Collections
              </a>
              <a href="/analytics" className="block w-full text-left px-3 py-2 text-sm border rounded-md hover:bg-gray-50">
                Analytics Dashboard
              </a>
            </div>
          </div>
        </div>
      )}
      
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Documents</h3>
          {recentDocuments.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent documents</p>
          ) : (
            <div className="space-y-2">
              {recentDocuments.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
                  <div>
                    <p className="text-sm font-medium">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {(doc.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">No recent activity</p>
          </div>
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
  )
}
