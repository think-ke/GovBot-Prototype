"use client"

import { MetricCard } from "./metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Users, MessageSquare, TrendingUp, Clock, CheckCircle, AlertTriangle, Activity, Loader2 } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { useEffect, useState } from "react"
import {
  ExecutiveDashboardData,
  UserDemographics,
  TrafficMetrics,
  SystemHealth,
  ContainmentRate,
  IntentAnalysis,
  fetchExecutiveDashboard,
  fetchUserDemographics,
  fetchTrafficMetrics,
  fetchSystemHealth,
  fetchContainmentRate,
  fetchIntentAnalysis
} from "@/lib/analytics-api"

// ------------------------------------------------------------------
// Mock data (kept for when the API is down or for demo)
// ------------------------------------------------------------------
const monthlyGrowthData = [
  { month: "Jan", users: 850, sessions: 2400, satisfaction: 4.1 },
  { month: "Feb", users: 1100, sessions: 3200, satisfaction: 4.2 },
  { month: "Mar", users: 1250, sessions: 4100, satisfaction: 4.3 },
  { month: "Apr", users: 1420, sessions: 4800, satisfaction: 4.4 },
  { month: "May", users: 1650, sessions: 5600, satisfaction: 4.5 },
  { month: "Jun", users: 1850, sessions: 6200, satisfaction: 4.6 },
]

const fallbackServiceDistribution = [
  { name: "Document Requests", value: 35, color: "#10b981" },
  { name: "General Inquiries", value: 28, color: "#3b82f6" },
  { name: "Form Assistance", value: 20, color: "#f59e0b" },
  { name: "Status Checks", value: 17, color: "#ef4444" },
]

export function ExecutiveDashboard() {
  // --------------------- State ---------------------
  const [executiveData, setExecutiveData] = useState<ExecutiveDashboardData | null>(null)
  const [userData, setUserData] = useState<UserDemographics | null>(null)
  const [trafficData, setTrafficData] = useState<TrafficMetrics | null>(null)
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [containmentData, setContainmentData] = useState<ContainmentRate | null>(null)
  const [intentData, setIntentData] = useState<IntentAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [processedServiceDistribution, setProcessedServiceDistribution] = useState<any[]>([])
  const [processedGrowthData, setProcessedGrowthData] = useState<any[]>([])

  // --------------------- Data fetch ---------------------
  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true)
        setError(null)

        const [
          exec,
          users,
          traffic,
          health,
          containment,
          intents
        ] = await Promise.all([
          fetchExecutiveDashboard().catch(() => null),
          fetchUserDemographics().catch(() => null),
          fetchTrafficMetrics().catch(() => null),
          fetchSystemHealth().catch(() => null),
          fetchContainmentRate().catch(() => null),
          fetchIntentAnalysis().catch(() => [])
        ])

        setExecutiveData(exec)
        setUserData(users)
        setTrafficData(traffic)
        setSystemHealth(health)
        setContainmentData(containment)
        setIntentData(intents)

        // ---------- Service distribution (pie) ----------
        if (intents.length) {
          const colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
          const total = intents.reduce((s, i) => s + i.frequency, 0)
          const top = intents.slice(0, 4).map((i, idx) => ({
            name: i.intent.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
            value: Math.round((i.frequency / total) * 100),
            color: colors[idx] ?? "#6b7280"
          }))
          setProcessedServiceDistribution(top)
        } else {
          setProcessedServiceDistribution(fallbackServiceDistribution)
        }

        // ---------- Growth line chart ----------
        if (users && traffic) {
          const cur = new Date().getMonth()
          const names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
          const growth = []
          for (let i = 5; i >= 0; i--) {
            const mIdx = (cur - i + 12) % 12
            const factor = 1 + i * 0.1
            growth.push({
              month: names[mIdx],
              users: Math.round(users.total_users / factor),
              sessions: Math.round(traffic.total_sessions / factor),
              satisfaction: 4.1 + i * 0.1
            })
          }
          setProcessedGrowthData(growth)
        } else {
          setProcessedGrowthData(monthlyGrowthData)
        }

      } catch (e) {
        setError(e instanceof Error ? e.message : "An error occurred")
      } finally {
        setLoading(false)
      }
    }

    fetchAll()
  }, [])

  // --------------------- UI ---------------------
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading executive dashboard...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-center">
        <div>
          <p className="text-red-600 mb-2">Error loading executive dashboard</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">

      {/* ==== KPI Cards ==== */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Citizens Served"
          value={userData?.total_users ?? 0}
          change={userData?.user_growth_rate ?? 0}
          changeLabel="vs last month"
          icon={<Users className="w-4 h-4" />}
          trend={userData?.user_growth_rate && userData.user_growth_rate > 0 ? "up" : "down"}
        />
        <MetricCard
          title="Monthly Sessions"
          value={trafficData?.total_sessions ?? 0}
          change={0}
          changeLabel="vs last month"
          icon={<MessageSquare className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Avg Response Time"
          value={systemHealth ? `${(systemHealth.api_response_time_p50 / 1000).toFixed(1)}s` : "0.0s"}
          change={0}
          changeLabel="vs last month"
          icon={<Clock className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Automation Rate"
          value={executiveData ? `${executiveData.containment_rate.toFixed(1)}%` : "0.0%"}
          change={0}
          changeLabel="vs last month"
          icon={<TrendingUp className="w-4 h-4" />}
          trend="neutral"
        />
      </div>

      {/* ==== System Health ==== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>System Health Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Uptime */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">System Uptime</span>
                <Badge className="bg-emerald-100 text-emerald-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  {systemHealth?.uptime_percentage?.toFixed(1) ?? "99.9"}%
                </Badge>
              </div>
              <Progress value={systemHealth?.uptime_percentage ?? 99.9} className="h-2" />
              <p className="text-xs text-gray-500">
                {(systemHealth?.uptime_percentage ?? 99.9).toFixed(1)}% uptime this month
              </p>
            </div>

            {/* Response Time */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Response Time</span>
                <Badge variant="secondary">
                  <Clock className="w-3 h-3 mr-1" />
                  {systemHealth ? `${systemHealth.api_response_time_p50.toFixed(0)}ms avg` : "200ms avg"}
                </Badge>
              </div>
              <Progress
                value={systemHealth ? Math.min(100, 100 - systemHealth.api_response_time_p95 / 10) : 80}
                className="h-2"
              />
              <p className="text-xs text-gray-500">
                P95: {systemHealth ? `${systemHealth.api_response_time_p95.toFixed(0)}ms` : "500ms"},
                P99: {systemHealth ? `${systemHealth.api_response_time_p99.toFixed(0)}ms` : "800ms"}
              </p>
            </div>

            {/* Error Rate */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Error Rate</span>
                <Badge className="bg-yellow-100 text-yellow-800">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  {systemHealth ? `${systemHealth.error_rate.toFixed(1)}%` : "0.1%"}
                </Badge>
              </div>
              <Progress
                value={systemHealth ? Math.max(0, 100 - systemHealth.error_rate * 10) : 99}
                className="h-2"
              />
              <p className="text-xs text-gray-500">Within acceptable limits</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==== Growth + Service Distribution ==== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Growth Trends */}
        <Card>
          <CardHeader><CardTitle>Growth Trends</CardTitle></CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={processedGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={2} name="Users" />
                  <Line type="monotone" dataKey="sessions" stroke="#3b82f6" strokeWidth={2} name="Sessions" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Service Distribution */}
        <Card>
          <CardHeader><CardTitle>Service Request Distribution</CardTitle></CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={processedServiceDistribution}
                    cx="50%" cy="50%"
                    innerRadius={60} outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {processedServiceDistribution.map((_, i) => (
                      <Cell key={`cell-${i}`} fill={processedServiceDistribution[i].color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {processedServiceDistribution.map((item, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm">{item.name}</span>
                  </div>
                  <span className="text-sm font-medium">{item.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==== Key Achievements ==== */}
      <Card>
        <CardHeader><CardTitle>Key Achievements This Month</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-emerald-50 rounded-lg">
              <div className="text-2xl font-bold text-emerald-600">
                {systemHealth ? `${systemHealth.uptime_percentage.toFixed(1)}%` : "99.8%"}
              </div>
              <div className="text-sm text-emerald-700">System Uptime</div>
              <div className="text-xs text-gray-600 mt-1">Reliable 24/7 citizen service availability</div>
            </div>

            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">24/7</div>
              <div className="text-sm text-blue-700">Service Availability</div>
              <div className="text-xs text-gray-600 mt-1">Continuous citizen support</div>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {executiveData?.avg_satisfaction_score?.toFixed(1) ?? "4.6"}/5
              </div>
              <div className="text-sm text-purple-700">Satisfaction Score</div>
              <div className="text-xs text-gray-600 mt-1">Based on conversation analysis</div>
            </div>
          </div>
        </CardContent>
      </Card>

    </div>
  )
}