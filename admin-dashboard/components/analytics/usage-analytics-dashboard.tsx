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

// Mock data
const hourlyTrafficData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i.toString().padStart(2, '0')}`,
  sessions: Math.floor(50 + Math.random() * 180),
  messages: Math.floor(120 + Math.random() * 450),
}))

const responseTimeData = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(day => ({
  day,
  p50: 140 + Math.random() * 60,
  p95: 350 + Math.random() * 150,
  p99: 550 + Math.random() * 250,
}))

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
        const [traffic, health, duration, peaks, errors] = await Promise.all([
          fetchTrafficMetrics().catch(() => null),
          fetchSystemHealth().catch(() => null),
          fetchSessionDuration().catch(() => null),
          fetchPeakHours(7).catch(() => []),
          fetchErrorAnalysis(24).catch(() => [])
        ])
        setTrafficMetrics(traffic)
        setSystemHealth(health)
        setSessionDuration(duration)
        setPeakHours(peaks)
        setErrorAnalysis(errors)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /><span className="ml-2">Loading...</span></div>
  if (error) return <div className="flex items-center justify-center h-64 text-center"><p className="text-red-600 mb-2">Error</p><p className="text-sm text-gray-600">{error}</p></div>

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Sessions" value={trafficMetrics?.total_sessions || 0} change={0} changeLabel="vs yesterday" icon={<Activity className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Total Messages" value={trafficMetrics?.total_messages || 0} change={0} changeLabel="vs yesterday" icon={<Globe className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Avg Response" value={systemHealth ? `${(systemHealth.api_response_time_p50 / 1000).toFixed(2)}s` : "0.18s"} change={0} icon={<Clock className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Uptime" value={systemHealth ? `${systemHealth.uptime_percentage.toFixed(1)}%` : "99.8%"} change={0} icon={<CheckCircle className="w-4 h-4" />} trend="neutral" />
      </div>

      {/* Hourly Traffic */}
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="w-5 h-5" /> Hourly Traffic</CardTitle></CardHeader>
        <CardContent>
          <div className="h-[350px]"><ResponsiveContainer><AreaChart data={hourlyTrafficData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="hour" /><YAxis /><Area type="monotone" dataKey="sessions" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} /><Area type="monotone" dataKey="messages" stackId="2" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} /></AreaChart></ResponsiveContainer></div>
        </CardContent>
      </Card>

      {/* Response + Duration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Server className="w-5 h-5" /> Response Time</CardTitle></CardHeader>
          <CardContent>
            <div className="h-[300px]"><ResponsiveContainer><LineChart data={responseTimeData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Line type="monotone" dataKey="p50" stroke="#10b981" /><Line type="monotone" dataKey="p95" stroke="#f59e0b" /><Line type="monotone" dataKey="p99" stroke="#ef4444" /></LineChart></ResponsiveContainer></div>
            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              {["P50", "P95", "P99"].map((p, i) => (
                <div key={i}>
                  <div className="text-sm text-gray-600">{p}</div>
                  <div className={`text-lg font-semibold ${i === 0 ? 'text-emerald-600' : i === 1 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {systemHealth ? `${systemHealth[`api_response_time_${p.toLowerCase()}` as keyof SystemHealth] as number}ms` : i === 0 ? "180ms" : i === 1 ? "450ms" : "680ms"}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Clock className="w-5 h-5" /> Session Duration</CardTitle></CardHeader>
          <CardContent>
            <div className="text-center mb-6">
              <div className="text-3xl font-bold text-blue-600">{sessionDuration ? `${sessionDuration.average_duration_minutes.toFixed(1)}` : "5.2"} min</div>
              <div className="text-sm text-gray-600">Average</div>
            </div>
            {[
              { label: "< 2 min", value: 25, color: "red" },
              { label: "2-10 min", value: 55, color: "yellow" },
              { label: "> 10 min", value: 20, color: "emerald" },
            ].map((s, i) => (
              <div key={i} className="flex justify-between items-center mb-3">
                <span className="text-sm">{s.label}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div className={`bg-${s.color}-500 h-2 rounded-full`} style={{ width: `${s.value}%` }} />
                  </div>
                  <span className="text-sm font-medium">{s.value}%</span>
                </div>
              </div>
            ))}
            <div className="pt-4 border-t text-center">
              <div className="text-lg font-semibold">{sessionDuration ? `${sessionDuration.median_duration_minutes.toFixed(1)}` : "3.8"} min</div>
              <div className="text-xs text-gray-500">Median</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Database className="w-5 h-5" /> System Health</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { icon: CheckCircle, value: systemHealth?.uptime_percentage.toFixed(1) || "99.8", label: "Uptime", color: "emerald" },
              { icon: Zap, value: systemHealth ? `${(systemHealth.api_response_time_p50 / 1000).toFixed(2)}s` : "0.18s", label: "Avg Response", color: "blue" },
              { icon: AlertTriangle, value: systemHealth?.error_rate.toFixed(2) || "0.12", label: "Error Rate", color: "yellow" },
              { icon: Globe, value: trafficMetrics?.unique_users || 1250, label: "Active Users", color: "purple" },
            ].map((item, i) => (
              <div key={i} className="text-center p-4 bg-${item.color}-50 rounded-lg">
                <item.icon className={`w-8 h-8 text-${item.color}-600 mx-auto mb-2`} />
                <div className="text-2xl font-bold text-${item.color}-600">{item.value}{item.label.includes("Rate") ? "%" : ""}</div>
                <div className="text-sm text-${item.color}-700">{item.label}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}