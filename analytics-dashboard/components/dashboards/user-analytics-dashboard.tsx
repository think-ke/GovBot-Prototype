import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, UserPlus, UserCheck, Clock, MapPin, Smartphone, Heart } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts"

// Mock data
const userGrowthData = [
  { month: "Jan", newUsers: 150, returningUsers: 700, totalUsers: 850 },
  { month: "Feb", newUsers: 250, returningUsers: 850, totalUsers: 1100 },
  { month: "Mar", newUsers: 150, returningUsers: 1100, totalUsers: 1250 },
  { month: "Apr", newUsers: 170, returningUsers: 1250, totalUsers: 1420 },
  { month: "May", newUsers: 230, returningUsers: 1420, totalUsers: 1650 },
  { month: "Jun", newUsers: 200, returningUsers: 1650, totalUsers: 1850 },
]

const sessionFrequencyData = [
  { range: "1 session", users: 420, percentage: 22.7 },
  { range: "2-5 sessions", users: 650, percentage: 35.1 },
  { range: "6-10 sessions", users: 480, percentage: 25.9 },
  { range: "11-20 sessions", users: 200, percentage: 10.8 },
  { range: "20+ sessions", users: 100, percentage: 5.4 },
]

const deviceDistribution = [
  { name: "Mobile", value: 65, color: "#10b981" },
  { name: "Desktop", value: 28, color: "#3b82f6" },
  { name: "Tablet", value: 7, color: "#f59e0b" },
]

const retentionData = [
  { period: "Day 1", rate: 65.5 },
  { period: "Day 7", rate: 42.3 },
  { period: "Day 30", rate: 28.7 },
  { period: "Day 90", rate: 18.2 },
]

const chartConfig = {
  newUsers: {
    label: "New Users",
    color: "#10b981",
  },
  returningUsers: {
    label: "Returning Users",
    color: "#3b82f6",
  },
  totalUsers: {
    label: "Total Users",
    color: "#f59e0b",
  },
}

export function UserAnalyticsDashboard() {
  return (
    <div className="space-y-6">
      {/* User Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={1850}
          change={18.2}
          changeLabel="vs last month"
          icon={<Users className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="New Users"
          value={200}
          change={-13.0}
          changeLabel="vs last month"
          icon={<UserPlus className="w-4 h-4" />}
          trend="down"
        />
        <MetricCard
          title="Active Users"
          value={1420}
          change={8.5}
          changeLabel="vs last month"
          icon={<UserCheck className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Avg Session Duration"
          value="8.5 min"
          change={5.2}
          changeLabel="vs last month"
          icon={<Clock className="w-4 h-4" />}
          trend="up"
        />
      </div>

      {/* User Growth and Session Frequency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>User Growth Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={userGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="newUsers" fill="var(--color-newUsers)" name="New Users" radius={[4, 4, 0, 0]} />
                  <Bar
                    dataKey="returningUsers"
                    fill="var(--color-returningUsers)"
                    name="Returning Users"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Frequency Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sessionFrequencyData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.range}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{item.users} users</span>
                      <Badge variant="secondary">{item.percentage}%</Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${item.percentage}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Device Distribution and User Retention */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Smartphone className="w-5 h-5" />
              <span>Device Distribution</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deviceDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {deviceDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip content={<ChartTooltipContent />} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
            <div className="mt-4 space-y-2">
              {deviceDistribution.map((item, index) => (
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

        <Card>
          <CardHeader>
            <CardTitle>User Retention Rates</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={retentionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* User Satisfaction and Geographic Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Heart className="w-5 h-5" />
              <span>User Satisfaction Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-emerald-600">4.6/5</div>
                <div className="text-sm text-gray-600">Overall Satisfaction Score</div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Positive Conversations</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-emerald-600 h-2 rounded-full" style={{ width: "75%" }} />
                    </div>
                    <span className="text-sm font-medium">75%</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Neutral Conversations</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-yellow-500 h-2 rounded-full" style={{ width: "20%" }} />
                    </div>
                    <span className="text-sm font-medium">20%</span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Escalation Rate</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div className="bg-red-500 h-2 rounded-full" style={{ width: "5%" }} />
                    </div>
                    <span className="text-sm font-medium">5%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MapPin className="w-5 h-5" />
              <span>Top User Locations</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { location: "Capital Region", users: 485, percentage: 26.2 },
                { location: "Northern Province", users: 320, percentage: 17.3 },
                { location: "Eastern District", users: 280, percentage: 15.1 },
                { location: "Southern Region", users: 245, percentage: 13.2 },
                { location: "Western Province", users: 210, percentage: 11.4 },
                { location: "Other Regions", users: 310, percentage: 16.8 },
              ].map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium">{item.location}</span>
                      <span className="text-sm text-gray-600">{item.users} users</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${item.percentage}%` }} />
                    </div>
                  </div>
                  <Badge variant="secondary" className="ml-3">
                    {item.percentage}%
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
