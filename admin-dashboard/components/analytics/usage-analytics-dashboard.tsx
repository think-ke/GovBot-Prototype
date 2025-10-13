"use client"

import { MetricCard } from "./metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Activity, Clock, AlertTriangle, CheckCircle, Zap, Server, Globe, Database, Loader2 } from "lucide-react"
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

// Mock data for demonstration
const hourlyTrafficData = [
  { hour: "00", sessions: 45, messages: 120 },
  { hour: "01", sessions: 32, messages: 89 },
  { hour: "02", sessions: 28, messages: 76 },
  { hour: "03", sessions: 25, messages: 68 },
  { hour: "04", sessions: 30, messages: 82 },
  { hour: "05", sessions: 38, messages: 105 },
  { hour: "06", sessions: 65, messages: 178 },
  { hour: "07", sessions: 95, messages: 260 },
  { hour: "08", sessions: 142, messages: 385 },
  { hour: "09", sessions: 186, messages: 505 },
  { hour: "10", sessions: 198, messages: 540 },
  { hour: "11", sessions: 205, messages: 558 },
  { hour: "12", sessions: 195, messages: 530 },
  { hour: "13", sessions: 210, messages: 572 },
  { hour: "14", sessions: 225, messages: 612 },
  { hour: "15", sessions: 218, messages: 594 },
  { hour: "16", sessions: 195, messages: 530 },
  { hour: "17", sessions: 168, messages: 456 },
  { hour: "18", sessions: 142, messages: 385 },
  { hour: "19", sessions: 118, messages: 321 },
  { hour: "20", sessions: 95, messages: 258 },
  { hour: "21", sessions: 78, messages: 212 },
  { hour: "22", sessions: 62, messages: 168 },
  { hour: "23", sessions: 51, messages: 138 },
]

const responseTimeData = [
  { day: "Mon", p50: 180, p95: 450, p99: 680 },
  { day: "Tue", p50: 165, p95: 420, p99: 650 },
  { day: "Wed", p50: 175, p95: 440, p99: 670 },
  { day: "Thu", p50: 190, p95: 480, p99: 720 },
  { day: "Fri", p50: 200, p95: 510, p99: 780 },
  { day: "Sat", p50: 155, p95: 380, p99: 590 },
  { day: "Sun", p50: 145, p95: 360, p99: 560 },
]

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
          fetchTrafficMetrics().catch(() => null),
          fetchSystemHealth().catch(() => null),
          fetchSessionDuration().catch(() => null),
          fetchPeakHours(7).catch(() => []),
          fetchErrorAnalysis(24).catch(() => [])
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
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading usage analytics...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading usage analytics</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Traffic Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Sessions"
          value={trafficMetrics?.total_sessions || 0}
          change={0}
          changeLabel="vs yesterday"
          icon={<Activity className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Total Messages"
          value={trafficMetrics?.total_messages || 0}
          change={0}
          changeLabel="vs yesterday"
          icon={<Globe className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Average Response Time"
          value={systemHealth ? `${(systemHealth.api_response_time_p50 / 1000).toFixed(2)}s` : "0.18s"}
          change={0}
          changeLabel="vs yesterday"
          icon={<Clock className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="System Uptime"
          value={systemHealth ? `${systemHealth.uptime_percentage.toFixed(1)}%` : "99.8%"}
          change={0}
          changeLabel="vs last week"
          icon={<CheckCircle className="w-4 h-4" />}
          trend="neutral"
        />
      </div>

      {/* Hourly Traffic Pattern */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>Hourly Traffic Pattern</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyTrafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Area
                  type="monotone"
                  dataKey="sessions"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                  name="Sessions"
                />
                <Area
                  type="monotone"
                  dataKey="messages"
                  stackId="2"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="Messages"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* System Performance and Session Duration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Server className="w-5 h-5" />
              <span>Response Time Trends</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Line type="monotone" dataKey="p50" stroke="#10b981" strokeWidth={2} name="P50" />
                  <Line type="monotone" dataKey="p95" stroke="#f59e0b" strokeWidth={2} name="P95" />
                  <Line type="monotone" dataKey="p99" stroke="#ef4444" strokeWidth={2} name="P99" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-sm text-gray-600">P50</div>
                <div className="text-lg font-semibold text-emerald-600">
                  {systemHealth ? `${systemHealth.api_response_time_p50.toFixed(0)}ms` : "180ms"}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">P95</div>
                <div className="text-lg font-semibold text-yellow-600">
                  {systemHealth ? `${systemHealth.api_response_time_p95.toFixed(0)}ms` : "450ms"}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">P99</div>
                <div className="text-lg font-semibold text-red-600">
                  {systemHealth ? `${systemHealth.api_response_time_p99.toFixed(0)}ms` : "680ms"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span>Session Duration Analysis</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">
                  {sessionDuration ? `${sessionDuration.average_duration_minutes.toFixed(1)}` : "5.2"} min
                </div>
                <div className="text-sm text-gray-600">Average Session Duration</div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Short Sessions (&lt; 2 min)</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-red-500 h-2 rounded-full" style={{ width: "25%" }} />
                    </div>
                    <span className="text-sm font-medium">25%</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Medium Sessions (2-10 min)</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-yellow-500 h-2 rounded-full" style={{ width: "55%" }} />
                    </div>
                    <span className="text-sm font-medium">55%</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Long Sessions (&gt; 10 min)</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full" style={{ width: "20%" }} />
                    </div>
                    <span className="text-sm font-medium">20%</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-700">
                    {sessionDuration ? `${sessionDuration.median_duration_minutes.toFixed(1)}` : "3.8"} min
                  </div>
                  <div className="text-xs text-gray-500">Median Duration</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="w-5 h-5" />
            <span>System Health Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-emerald-50 rounded-lg">
              <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-emerald-600">
                {systemHealth ? `${systemHealth.uptime_percentage.toFixed(1)}%` : "99.8%"}
              </div>
              <div className="text-sm text-emerald-700">Uptime</div>
              <div className="text-xs text-gray-600 mt-1">Last 30 days</div>
            </div>

            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Zap className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-600">
                {systemHealth ? `${(systemHealth.api_response_time_p50 / 1000).toFixed(2)}s` : "0.18s"}
              </div>
              <div className="text-sm text-blue-700">Avg Response</div>
              <div className="text-xs text-gray-600 mt-1">P50 latency</div>
            </div>

            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-yellow-600">
                {systemHealth ? `${systemHealth.error_rate.toFixed(2)}%` : "0.12%"}
              </div>
              <div className="text-sm text-yellow-700">Error Rate</div>
              <div className="text-xs text-gray-600 mt-1">Last 24 hours</div>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <Globe className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-purple-600">
                {trafficMetrics?.unique_users || 1250}
              </div>
              <div className="text-sm text-purple-700">Active Users</div>
              <div className="text-xs text-gray-600 mt-1">Current period</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Peak Usage Times */}
      <Card>
        <CardHeader>
          <CardTitle>Peak Usage Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Peak Hours</h4>
              <div className="space-y-2">
                {[
                  { time: "2:00 PM - 3:00 PM", load: 95 },
                  { time: "10:00 AM - 11:00 AM", load: 88 },
                  { time: "11:00 AM - 12:00 PM", load: 85 },
                  { time: "1:00 PM - 2:00 PM", load: 82 },
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{item.time}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${item.load}%` }} />
                      </div>
                      <span className="text-sm font-medium w-8">{item.load}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Peak Days</h4>
              <div className="space-y-2">
                {[
                  { day: "Wednesday", load: 92 },
                  { day: "Thursday", load: 89 },
                  { day: "Tuesday", load: 86 },
                  { day: "Monday", load: 83 },
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{item.day}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${item.load}%` }} />
                      </div>
                      <span className="text-sm font-medium w-8">{item.load}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Resource Usage</h4>
              <div className="space-y-2">
                {[
                  { resource: "CPU Usage", load: 45 },
                  { resource: "Memory Usage", load: 62 },
                  { resource: "Network I/O", load: 38 },
                  { resource: "Storage I/O", load: 28 },
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm">{item.resource}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            item.load > 80 ? 'bg-red-600' : 
                            item.load > 60 ? 'bg-yellow-600' : 'bg-emerald-600'
                          }`} 
                          style={{ width: `${item.load}%` }} 
                        />
                      </div>
                      <span className="text-sm font-medium w-8">{item.load}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
