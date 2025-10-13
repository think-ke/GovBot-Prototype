import { MetricCard } from "./metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, UserPlus, UserCheck, Clock, MapPin, Smartphone, Heart, Loader2 } from "lucide-react"
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
import { useEffect, useState } from "react"
import {
  UserDemographics,
  SessionFrequency,
  UserSentiment,
  RetentionData,
  fetchUserDemographics,
  fetchSessionFrequency,
  fetchUserSentiment,
  fetchUserRetention
} from "@/lib/analytics-api"

// Mock data for features not yet implemented in API
const deviceDistribution = [
  { name: "Mobile", value: 65, color: "#10b981" },
  { name: "Desktop", value: 28, color: "#3b82f6" },
  { name: "Tablet", value: 7, color: "#f59e0b" },
]

export function UserAnalyticsDashboard() {
  // State for API data
  const [demographics, setDemographics] = useState<UserDemographics | null>(null)
  const [sessionFrequencyData, setSessionFrequencyData] = useState<SessionFrequency[]>([])
  const [sentimentData, setSentimentData] = useState<UserSentiment | null>(null)
  const [retentionData, setRetentionData] = useState<RetentionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Processed data for charts
  const [processedSessionFrequency, setProcessedSessionFrequency] = useState<any[]>([])
  const [processedRetention, setProcessedRetention] = useState<any[]>([])

  // Fetch data on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const [demographicsData, sessionData, sentimentDataResult, retentionDataResult] = await Promise.all([
          fetchUserDemographics().catch(() => null),
          fetchSessionFrequency().catch(() => []),
          fetchUserSentiment().catch(() => null),
          fetchUserRetention().catch(() => null)
        ])

        setDemographics(demographicsData)
        setSessionFrequencyData(sessionData)
        setSentimentData(sentimentDataResult)
        setRetentionData(retentionDataResult)

        // Process session frequency data for charts
        if (sessionData.length > 0) {
          const sessionRanges = [
            { range: "1 session", min: 1, max: 1 },
            { range: "2-5 sessions", min: 2, max: 5 },
            { range: "6-10 sessions", min: 6, max: 10 },
            { range: "11-20 sessions", min: 11, max: 20 },
            { range: "20+ sessions", min: 21, max: Infinity },
          ]

          const totalUsers = sessionData.length
          const processedFrequency = sessionRanges.map(range => {
            const users = sessionData.filter(user => 
              user.total_sessions >= range.min && user.total_sessions <= range.max
            ).length
            return {
              range: range.range,
              users,
              percentage: totalUsers > 0 ? (users / totalUsers * 100) : 0
            }
          })
          setProcessedSessionFrequency(processedFrequency)
        } else {
          // Mock data if no session data available
          setProcessedSessionFrequency([
            { range: "1 session", users: 320, percentage: 42 },
            { range: "2-5 sessions", users: 245, percentage: 32 },
            { range: "6-10 sessions", users: 125, percentage: 16 },
            { range: "11-20 sessions", users: 55, percentage: 7 },
            { range: "20+ sessions", users: 25, percentage: 3 },
          ])
        }

        // Process retention data for charts
        if (retentionDataResult) {
          const retention = [
            { period: "Day 1", rate: retentionDataResult.day_1_retention },
            { period: "Day 7", rate: retentionDataResult.day_7_retention },
            { period: "Day 30", rate: retentionDataResult.day_30_retention },
          ]
          setProcessedRetention(retention)
        } else {
          // Mock retention data
          setProcessedRetention([
            { period: "Day 1", rate: 85 },
            { period: "Day 7", rate: 62 },
            { period: "Day 30", rate: 45 },
          ])
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading user analytics...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading user analytics</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* User Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={demographics?.total_users || 0}
          change={demographics?.user_growth_rate || 0}
          changeLabel="vs last month"
          icon={<Users className="w-4 h-4" />}
          trend={demographics?.user_growth_rate && demographics.user_growth_rate > 0 ? "up" : "down"}
        />
        <MetricCard
          title="New Users"
          value={demographics?.new_users || 0}
          change={0} // Would need additional API data for change calculation
          changeLabel="vs last month"
          icon={<UserPlus className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Active Users"
          value={demographics?.active_users || 0}
          change={0} // Would need additional API data for change calculation
          changeLabel="vs last month"
          icon={<UserCheck className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Returning Users"
          value={demographics?.returning_users || 0}
          change={0} // Would need additional API data for change calculation
          changeLabel="vs last month"
          icon={<Clock className="w-4 h-4" />}
          trend="neutral"
        />
      </div>

      {/* User Growth and Session Frequency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>User Growth Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-emerald-50 rounded-lg">
                  <div className="text-2xl font-bold text-emerald-600">
                    {demographics?.total_users || 0}
                  </div>
                  <div className="text-sm text-emerald-700">Total Users</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {demographics?.new_users || 0}
                  </div>
                  <div className="text-sm text-blue-700">New Users</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {demographics?.active_users || 0}
                  </div>
                  <div className="text-sm text-orange-700">Active Users</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {demographics?.returning_users || 0}
                  </div>
                  <div className="text-sm text-purple-700">Returning Users</div>
                </div>
              </div>
              <div className="text-center text-sm text-gray-600">
                Growth Rate: {demographics?.user_growth_rate?.toFixed(1) || 0}%
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Frequency Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {processedSessionFrequency.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.range}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{item.users} users</span>
                      <Badge variant="secondary">{item.percentage.toFixed(1)}%</Badge>
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
            <div className="h-[250px]">
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
                </PieChart>
              </ResponsiveContainer>
            </div>
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
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={processedRetention}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
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
                <div className="text-3xl font-bold text-emerald-600">
                  {sentimentData?.satisfaction_score?.toFixed(1) || '4.2'}/5
                </div>
                <div className="text-sm text-gray-600">Overall Satisfaction Score</div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Positive Conversations</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-emerald-600 h-2 rounded-full" 
                        style={{ 
                          width: `${sentimentData ? 
                            (sentimentData.positive_conversations / 
                            (sentimentData.positive_conversations + sentimentData.neutral_conversations + sentimentData.negative_conversations) * 100) 
                            : 72}%` 
                        }} 
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {sentimentData ? 
                        Math.round(sentimentData.positive_conversations / 
                        (sentimentData.positive_conversations + sentimentData.neutral_conversations + sentimentData.negative_conversations) * 100) 
                        : 72}%
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Neutral Conversations</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full" 
                        style={{ 
                          width: `${sentimentData ? 
                            (sentimentData.neutral_conversations / 
                            (sentimentData.positive_conversations + sentimentData.neutral_conversations + sentimentData.negative_conversations) * 100) 
                            : 22}%` 
                        }} 
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {sentimentData ? 
                        Math.round(sentimentData.neutral_conversations / 
                        (sentimentData.positive_conversations + sentimentData.neutral_conversations + sentimentData.negative_conversations) * 100) 
                        : 22}%
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm">Escalation Rate</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full" 
                        style={{ width: `${sentimentData?.escalation_rate || 3.2}%` }} 
                      />
                    </div>
                    <span className="text-sm font-medium">{sentimentData?.escalation_rate?.toFixed(1) || 3.2}%</span>
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
