import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Users, MessageSquare, TrendingUp, Clock, CheckCircle, AlertTriangle, Activity } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"

// Mock data for demonstration
const monthlyGrowthData = [
  { month: "Jan", users: 850, sessions: 2400, satisfaction: 4.1 },
  { month: "Feb", users: 1100, sessions: 3200, satisfaction: 4.2 },
  { month: "Mar", users: 1250, sessions: 4100, satisfaction: 4.3 },
  { month: "Apr", users: 1420, sessions: 4800, satisfaction: 4.4 },
  { month: "May", users: 1650, sessions: 5600, satisfaction: 4.5 },
  { month: "Jun", users: 1850, sessions: 6200, satisfaction: 4.6 },
]

const serviceDistribution = [
  { name: "Document Requests", value: 35, color: "#10b981" },
  { name: "General Inquiries", value: 28, color: "#3b82f6" },
  { name: "Form Assistance", value: 20, color: "#f59e0b" },
  { name: "Status Checks", value: 17, color: "#ef4444" },
]

const chartConfig = {
  users: {
    label: "Users",
    color: "#10b981",
  },
  sessions: {
    label: "Sessions",
    color: "#3b82f6",
  },
  satisfaction: {
    label: "Satisfaction",
    color: "#f59e0b",
  },
}

export function ExecutiveDashboard() {
  return (
    <div className="space-y-6">
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Citizens Served"
          value={1850}
          change={18.2}
          changeLabel="vs last month"
          icon={<Users className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Monthly Sessions"
          value={6200}
          change={12.5}
          changeLabel="vs last month"
          icon={<MessageSquare className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Avg Response Time"
          value="1.2s"
          change={-15.3}
          changeLabel="vs last month"
          icon={<Clock className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Automation Rate"
          value="85.0%"
          change={2.3}
          changeLabel="vs last month"
          icon={<TrendingUp className="w-4 h-4" />}
          trend="up"
        />
      </div>

      {/* System Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>System Health Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">System Uptime</span>
                <Badge className="bg-emerald-100 text-emerald-800">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Healthy
                </Badge>
              </div>
              <Progress value={99.8} className="h-2" />
              <p className="text-xs text-gray-500">99.8% uptime this month</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Response Time</span>
                <Badge variant="secondary">
                  <Clock className="w-3 h-3 mr-1" />
                  150ms avg
                </Badge>
              </div>
              <Progress value={85} className="h-2" />
              <p className="text-xs text-gray-500">P95: 450ms, P99: 850ms</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Error Rate</span>
                <Badge className="bg-yellow-100 text-yellow-800">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  2.1%
                </Badge>
              </div>
              <Progress value={2.1} className="h-2" />
              <p className="text-xs text-gray-500">Within acceptable limits</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Growth Trends and Service Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Growth Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line type="monotone" dataKey="users" stroke="var(--color-users)" strokeWidth={2} name="Users" />
                  <Line
                    type="monotone"
                    dataKey="sessions"
                    stroke="var(--color-sessions)"
                    strokeWidth={2}
                    name="Sessions"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Service Request Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={serviceDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {serviceDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip content={<ChartTooltipContent />} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
            <div className="mt-4 space-y-2">
              {serviceDistribution.map((item, index) => (
                <div key={index} className="flex items-center justify-between">
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

      {/* Key Achievements */}
      <Card>
        <CardHeader>
          <CardTitle>Key Achievements This Month</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-emerald-50 rounded-lg">
              <div className="text-2xl font-bold text-emerald-600">99.8%</div>
              <div className="text-sm text-emerald-700">System Uptime</div>
              <div className="text-xs text-gray-600 mt-1">Reliable 24/7 citizen service availability</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">24/7</div>
              <div className="text-sm text-blue-700">Service Availability</div>
              <div className="text-xs text-gray-600 mt-1">Continuous citizen support</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">4.6/5</div>
              <div className="text-sm text-purple-700">Satisfaction Score</div>
              <div className="text-xs text-gray-600 mt-1">Based on conversation analysis</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
