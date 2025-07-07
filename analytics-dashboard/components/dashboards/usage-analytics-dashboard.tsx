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

// Mock data
const trafficData = [
  { hour: "00:00", sessions: 45, messages: 120, responseTime: 145 },
  { hour: "02:00", sessions: 32, messages: 85, responseTime: 132 },
  { hour: "04:00", sessions: 28, messages: 75, responseTime: 128 },
  { hour: "06:00", sessions: 65, messages: 180, responseTime: 155 },
  { hour: "08:00", sessions: 120, messages: 340, responseTime: 165 },
  { hour: "10:00", sessions: 220, messages: 620, responseTime: 185 },
  { hour: "12:00", sessions: 180, messages: 510, responseTime: 175 },
  { hour: "14:00", sessions: 245, messages: 695, responseTime: 195 },
  { hour: "16:00", sessions: 210, messages: 590, responseTime: 180 },
  { hour: "18:00", sessions: 165, messages: 465, responseTime: 170 },
  { hour: "20:00", sessions: 95, messages: 270, responseTime: 160 },
  { hour: "22:00", sessions: 68, messages: 190, responseTime: 150 },
]

const sessionDurationData = [
  { duration: "0-1 min", count: 320, percentage: 15.5 },
  { duration: "1-5 min", count: 935, percentage: 45.2 },
  { duration: "5-10 min", count: 520, percentage: 25.1 },
  { duration: "10-20 min", count: 210, percentage: 10.1 },
  { duration: "20+ min", count: 85, percentage: 4.1 },
]

const systemMetrics = [
  { metric: "CPU Usage", value: 45, status: "healthy", threshold: 80 },
  { metric: "Memory Usage", value: 62, status: "healthy", threshold: 85 },
  { metric: "Database Connections", value: 35, status: "healthy", threshold: 90 },
  { metric: "API Rate Limit", value: 28, status: "healthy", threshold: 95 },
]

const errorData = [
  { time: "00:00", errors: 2, total: 145 },
  { time: "04:00", errors: 1, total: 128 },
  { time: "08:00", errors: 5, total: 340 },
  { time: "12:00", errors: 8, total: 510 },
  { time: "16:00", errors: 6, total: 590 },
  { time: "20:00", errors: 3, total: 270 },
]

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
  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="System Uptime"
          value="99.8%"
          change={0.2}
          changeLabel="vs last month"
          icon={<CheckCircle className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Avg Response Time"
          value="150ms"
          change={-8.5}
          changeLabel="vs last month"
          icon={<Zap className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Error Rate"
          value="2.1%"
          change={-0.3}
          changeLabel="vs last month"
          icon={<AlertTriangle className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Peak Concurrent Users"
          value={245}
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
                  <span>Database Connections</span>
                  <span>35/100</span>
                </div>
                <Progress value={35} className="h-2" />

                <div className="flex justify-between text-sm">
                  <span>API Rate Limit</span>
                  <span>2,800/10,000</span>
                </div>
                <Progress value={28} className="h-2" />

                <div className="flex justify-between text-sm">
                  <span>Storage Usage</span>
                  <span>45/100 GB</span>
                </div>
                <Progress value={45} className="h-2" />
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Performance SLA</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Response Time {"<"} 500ms</span>
                  <Badge className="bg-emerald-100 text-emerald-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Met
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Uptime {">"} 99.5%</span>
                  <Badge className="bg-emerald-100 text-emerald-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Met
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Error Rate {"<"} 5%</span>
                  <Badge className="bg-emerald-100 text-emerald-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Met
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
