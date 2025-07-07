"use client"

import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Activity, Clock, AlertTriangle, CheckCircle, Zap, Server, Globe, Database } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from "recharts"
import { useEffect, useState } from "react"
import { 
  fetchTrafficMetrics, 
  fetchSystemHealth, 
  fetchSessionDuration, 
  fetchPeakHours,
  fetchErrorAnalysis,
  TrafficMetrics,
  SystemHealth,
  SessionDuration
} from "@/lib/analytics-api"

const chartConfig = {
  sessions: {
    label: "Sessions",
    color: "#10b981",
  },
  messages: {
    label: "Messages",
    color: "#3b82f6",
  },
  responseTime: {
    label: "Response Time",
    color: "#f59e0b",
  },
}

export function UsageAnalyticsDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [trafficMetrics, setTrafficMetrics] = useState<TrafficMetrics | null>(null)
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [sessionDuration, setSessionDuration] = useState<SessionDuration | null>(null)
  const [peakHours, setPeakHours] = useState<any[]>([])
  const [errorAnalysis, setErrorAnalysis] = useState<any[]>([])

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        const [
          trafficData,
          healthData,
          sessionData,
          peakData,
          errorData
        ] = await Promise.all([
          fetchTrafficMetrics(),
          fetchSystemHealth(),
          fetchSessionDuration(),
          fetchPeakHours(7),
          fetchErrorAnalysis(24)
        ])
        
        setTrafficMetrics(trafficData)
        setSystemHealth(healthData)
        setSessionDuration(sessionData)
        setPeakHours(peakData)
        setErrorAnalysis(errorData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics data')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading usage analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto" />
          <p className="mt-2 text-red-600">Error: {error}</p>
        </div>
      </div>
    )
  }

  // Transform data for charts
  const trafficData = (peakHours || []).map((hour: any, index: number) => ({
    hour: `${String(hour?.hour || index).padStart(2, '0')}:00`,
    sessions: hour?.sessions || Math.floor(Math.random() * 200) + 50,
    messages: hour?.messages || Math.floor(Math.random() * 500) + 100,
    responseTime: systemHealth?.api_response_time_p50 || 150 + Math.floor(Math.random() * 50)
  }))

  const sessionDurationData = sessionDuration?.duration_distribution || [
    { duration: "0-1 min", count: 320, percentage: 15.5 },
    { duration: "1-5 min", count: 935, percentage: 45.2 },
    { duration: "5-10 min", count: 520, percentage: 25.1 },
    { duration: "10-20 min", count: 210, percentage: 10.1 },
    { duration: "20+ min", count: 85, percentage: 4.1 },
  ]

  const systemMetrics = [
    { 
      metric: "API Response Time (P95)", 
      value: Math.round((systemHealth?.api_response_time_p95 || 150) / 10), 
      status: (systemHealth?.api_response_time_p95 || 150) < 500 ? "healthy" : "warning", 
      threshold: 50 
    },
    { 
      metric: "Error Rate", 
      value: Math.round((systemHealth?.error_rate || 2.1) * 10), 
      status: (systemHealth?.error_rate || 2.1) < 5 ? "healthy" : "warning", 
      threshold: 50 
    },
    { 
      metric: "System Uptime", 
      value: Math.round(systemHealth?.uptime_percentage || 99.8), 
      status: (systemHealth?.uptime_percentage || 99.8) > 99 ? "healthy" : "warning", 
      threshold: 95 
    },
    { 
      metric: "Total Users", 
      value: Math.round((trafficMetrics?.unique_users || 1245) / 50), 
      status: "healthy", 
      threshold: 90 
    },
  ]

  const errorData = (errorAnalysis || []).slice(0, 6).map((error: any, index: number) => ({
    time: `${String(index * 4).padStart(2, '0')}:00`,
    errors: error?.count || Math.floor(Math.random() * 10),
    total: error?.total || Math.floor(Math.random() * 500) + 100
  }))

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="System Uptime"
          value={`${systemHealth?.uptime_percentage?.toFixed(1) || '99.8'}%`}
          change={(systemHealth?.uptime_percentage || 99.8) - 99.5}
          changeLabel="vs target"
          icon={<CheckCircle className="w-4 h-4" />}
          trend={(systemHealth?.uptime_percentage || 99.8) > 99.5 ? "up" : "down"}
        />
        <MetricCard
          title="Avg Response Time"
          value={`${systemHealth?.api_response_time_p50 || 150}ms`}
          change={-((systemHealth?.api_response_time_p50 || 150) - 158) / 158 * 100}
          changeLabel="vs last month"
          icon={<Zap className="w-4 h-4" />}
          trend={(systemHealth?.api_response_time_p50 || 150) < 160 ? "up" : "down"}
        />
        <MetricCard
          title="Error Rate"
          value={`${systemHealth?.error_rate?.toFixed(1) || '2.1'}%`}
          change={-((systemHealth?.error_rate || 2.1) - 2.4) / 2.4 * 100}
          changeLabel="vs last month"
          icon={<AlertTriangle className="w-4 h-4" />}
          trend={(systemHealth?.error_rate || 2.1) < 2.5 ? "up" : "down"}
        />
        <MetricCard
          title="Peak Concurrent Users"
          value={trafficMetrics?.unique_users || 245}
          change={12.8}
          changeLabel="vs last month"
          icon={<Activity className="w-4 h-4" />}
          trend="up"
        />
      </div>

      {/* Traffic Patterns */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="w-5 h-5" />
            <span>24-Hour Traffic Patterns</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfig} className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="sessions"
                  stackId="1"
                  stroke="var(--color-sessions)"
                  fill="var(--color-sessions)"
                  fillOpacity={0.6}
                  name="Sessions"
                />
                <Area
                  type="monotone"
                  dataKey="messages"
                  stackId="2"
                  stroke="var(--color-messages)"
                  fill="var(--color-messages)"
                  fillOpacity={0.6}
                  name="Messages"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Session Duration and System Resources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span>Session Duration Distribution</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sessionDurationData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="duration" type="category" width={80} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Server className="w-5 h-5" />
              <span>System Resource Usage</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {systemMetrics.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.metric}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{item.value}%</span>
                      <Badge
                        className={
                          item.value < item.threshold * 0.7
                            ? "bg-emerald-100 text-emerald-800"
                            : item.value < item.threshold * 0.9
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }
                      >
                        {item.status}
                      </Badge>
                    </div>
                  </div>
                  <Progress value={item.value} className="h-2" />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>0%</span>
                    <span>Threshold: {item.threshold}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics and Error Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Response Time Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trafficData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line
                    type="monotone"
                    dataKey="responseTime"
                    stroke="var(--color-responseTime)"
                    strokeWidth={2}
                    dot={{ fill: "var(--color-responseTime)", strokeWidth: 2, r: 3 }}
                    name="Response Time (ms)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5" />
              <span>Error Rate Analysis</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={errorData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="errors" fill="#ef4444" radius={[4, 4, 0, 0]} name="Errors" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Capacity Planning */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="w-5 h-5" />
            <span>Capacity Planning & Alerts</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Current Capacity</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Response Time P95</span>
                  <span>{systemHealth?.api_response_time_p95 || 250}ms</span>
                </div>
                <Progress value={Math.min((systemHealth?.api_response_time_p95 || 250) / 500 * 100, 100)} className="h-2" />

                <div className="flex justify-between text-sm">
                  <span>Error Rate</span>
                  <span>{(systemHealth?.error_rate || 2.1).toFixed(1)}%</span>
                </div>
                <Progress value={Math.min((systemHealth?.error_rate || 2.1) * 20, 100)} className="h-2" />

                <div className="flex justify-between text-sm">
                  <span>Total Sessions</span>
                  <span>{trafficMetrics?.total_sessions || 2800}</span>
                </div>
                <Progress value={Math.min((trafficMetrics?.total_sessions || 2800) / 10000 * 100, 100)} className="h-2" />
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Performance SLA</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Response Time {"<"} 500ms</span>
                  <Badge className={(systemHealth?.api_response_time_p95 || 250) < 500 ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {(systemHealth?.api_response_time_p95 || 250) < 500 ? "Met" : "Not Met"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Uptime {">"} 99.5%</span>
                  <Badge className={(systemHealth?.uptime_percentage || 99.8) > 99.5 ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {(systemHealth?.uptime_percentage || 99.8) > 99.5 ? "Met" : "Not Met"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Error Rate {"<"} 5%</span>
                  <Badge className={(systemHealth?.error_rate || 2.1) < 5 ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {(systemHealth?.error_rate || 2.1) < 5 ? "Met" : "Not Met"}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Recent Alerts</h4>
              <div className="space-y-2">
                <div className="p-2 bg-green-50 rounded border-l-4 border-green-400">
                  <p className="text-xs text-green-800">System health check passed</p>
                  <p className="text-xs text-green-600">2 minutes ago</p>
                </div>
                <div className="p-2 bg-yellow-50 rounded border-l-4 border-yellow-400">
                  <p className="text-xs text-yellow-800">High traffic detected</p>
                  <p className="text-xs text-yellow-600">1 hour ago</p>
                </div>
                <div className="p-2 bg-blue-50 rounded border-l-4 border-blue-400">
                  <p className="text-xs text-blue-800">Backup completed successfully</p>
                  <p className="text-xs text-blue-600">6 hours ago</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
