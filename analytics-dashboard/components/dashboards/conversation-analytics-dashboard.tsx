import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, FileText, Target, TrendingDown, Brain, Search, Users, CheckCircle } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, LineChart, Line } from "recharts"

// Mock data
const conversationFlowData = [
  { turn: 1, completionRate: 95.2, abandonment: 4.8, avgResponseTime: 1.2 },
  { turn: 2, completionRate: 88.5, abandonment: 11.5, avgResponseTime: 1.4 },
  { turn: 3, completionRate: 82.1, abandonment: 17.9, avgResponseTime: 1.6 },
  { turn: 4, completionRate: 75.8, abandonment: 24.2, avgResponseTime: 1.8 },
  { turn: 5, completionRate: 68.9, abandonment: 31.1, avgResponseTime: 2.1 },
  { turn: "6+", completionRate: 58.3, abandonment: 41.7, avgResponseTime: 2.5 },
]

const intentAnalysisData = [
  { intent: "Document Request", frequency: 450, successRate: 92.5, avgTurns: 2.1 },
  { intent: "Form Assistance", frequency: 320, successRate: 88.2, avgTurns: 3.2 },
  { intent: "Status Inquiry", frequency: 280, successRate: 95.1, avgTurns: 1.8 },
  { intent: "General Information", frequency: 240, successRate: 85.7, avgTurns: 2.8 },
  { intent: "Complaint/Issue", frequency: 180, successRate: 72.3, avgTurns: 4.5 },
  { intent: "Service Application", frequency: 150, successRate: 78.9, avgTurns: 3.8 },
]

const documentRetrievalData = [
  { type: "Government Forms", frequency: 380, successRate: 94.2, collection: "gov_forms_2024" },
  { type: "Policy Documents", frequency: 220, successRate: 89.1, collection: "policies" },
  { type: "Service Guides", frequency: 180, successRate: 91.7, collection: "guides" },
  { type: "Legal Documents", frequency: 120, successRate: 86.5, collection: "legal" },
  { type: "FAQ Resources", frequency: 95, successRate: 97.8, collection: "faqs" },
]

const sentimentTrends = [
  { time: "Week 1", positive: 72, neutral: 23, negative: 5 },
  { time: "Week 2", positive: 75, neutral: 20, negative: 5 },
  { time: "Week 3", positive: 78, neutral: 18, negative: 4 },
  { time: "Week 4", positive: 76, neutral: 19, negative: 5 },
]

const dropOffPoints = [
  { stage: "Initial Query", users: 1000, percentage: 100 },
  { stage: "First Response", users: 950, percentage: 95 },
  { stage: "Follow-up", users: 820, percentage: 82 },
  { stage: "Document Access", users: 680, percentage: 68 },
  { stage: "Resolution", users: 580, percentage: 58 },
]

const chartConfig = {
  completionRate: {
    label: "Completion Rate",
    color: "#10b981",
  },
  abandonment: {
    label: "Abandonment Rate",
    color: "#ef4444",
  },
  positive: {
    label: "Positive",
    color: "#10b981",
  },
  neutral: {
    label: "Neutral",
    color: "#f59e0b",
  },
  negative: {
    label: "Negative",
    color: "#ef4444",
  },
}

export function ConversationAnalyticsDashboard() {
  return (
    <div className="space-y-6">
      {/* Conversation Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Avg Turns per Conversation"
          value="2.8"
          change={-5.2}
          changeLabel="vs last month"
          icon={<MessageSquare className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Document Retrieval Success"
          value="92.3%"
          change={3.1}
          changeLabel="vs last month"
          icon={<FileText className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Intent Recognition Rate"
          value="89.7%"
          change={2.8}
          changeLabel="vs last month"
          icon={<Target className="w-4 h-4" />}
          trend="up"
        />
        <MetricCard
          title="Conversation Drop-off"
          value="24.2%"
          change={-8.5}
          changeLabel="vs last month"
          icon={<TrendingDown className="w-4 h-4" />}
          trend="up"
        />
      </div>

      {/* Conversation Flow Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="w-5 h-5" />
            <span>Conversation Flow Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfig} className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={conversationFlowData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="turn" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="completionRate"
                  stroke="var(--color-completionRate)"
                  strokeWidth={3}
                  dot={{ fill: "var(--color-completionRate)", strokeWidth: 2, r: 4 }}
                  name="Completion Rate (%)"
                />
                <Line
                  type="monotone"
                  dataKey="abandonment"
                  stroke="var(--color-abandonment)"
                  strokeWidth={3}
                  dot={{ fill: "var(--color-abandonment)", strokeWidth: 2, r: 4 }}
                  name="Abandonment Rate (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Intent Analysis and Document Retrieval */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="w-5 h-5" />
              <span>Top User Intents</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {intentAnalysisData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.intent}</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{item.frequency} queries</Badge>
                      <Badge
                        className={
                          item.successRate > 90
                            ? "bg-emerald-100 text-emerald-800"
                            : item.successRate > 80
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }
                      >
                        {item.successRate}%
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${(item.frequency / 450) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Avg turns: {item.avgTurns}</span>
                    <span>Success: {item.successRate}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="w-5 h-5" />
              <span>Document Retrieval Performance</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={documentRetrievalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="frequency" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Access Frequency" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Sentiment Trends and Drop-off Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Conversation Sentiment Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig} className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sentimentTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar
                    dataKey="positive"
                    stackId="a"
                    fill="var(--color-positive)"
                    name="Positive"
                    radius={[0, 0, 0, 0]}
                  />
                  <Bar dataKey="neutral" stackId="a" fill="var(--color-neutral)" name="Neutral" radius={[0, 0, 0, 0]} />
                  <Bar
                    dataKey="negative"
                    stackId="a"
                    fill="var(--color-negative)"
                    name="Negative"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-5 h-5" />
              <span>Conversation Drop-off Funnel</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dropOffPoints.map((stage, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{stage.stage}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{stage.users} users</span>
                      <Badge variant="secondary">{stage.percentage}%</Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-emerald-600 to-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${stage.percentage}%` }}
                    />
                  </div>
                  {index < dropOffPoints.length - 1 && (
                    <div className="text-xs text-red-600 ml-2">
                      Drop-off: {dropOffPoints[index].users - dropOffPoints[index + 1].users} users
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content Performance and Knowledge Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Content Performance Analysis</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-emerald-50 rounded-lg">
                  <div className="text-2xl font-bold text-emerald-600">94.2%</div>
                  <div className="text-sm text-emerald-700">Retrieval Success</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">2.1s</div>
                  <div className="text-sm text-blue-700">Avg Retrieval Time</div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Top Performing Collections</h4>
                {documentRetrievalData.slice(0, 3).map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">{item.type}</span>
                    <div className="flex items-center space-x-2">
                      <Badge className="bg-emerald-100 text-emerald-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        {item.successRate}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Knowledge Gaps & Improvement Areas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                <h4 className="font-medium text-yellow-800">Identified Gaps</h4>
                <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                  <li>• Complex tax calculation queries (12% failure rate)</li>
                  <li>• Multi-step application processes (18% abandonment)</li>
                  <li>• Regional-specific regulations (8% escalation rate)</li>
                </ul>
              </div>

              <div className="p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                <h4 className="font-medium text-blue-800">Recommended Actions</h4>
                <ul className="mt-2 space-y-1 text-sm text-blue-700">
                  <li>• Add tax calculation examples to knowledge base</li>
                  <li>• Create step-by-step process guides</li>
                  <li>• Expand regional content coverage</li>
                </ul>
              </div>

              <div className="p-3 bg-emerald-50 border-l-4 border-emerald-400 rounded">
                <h4 className="font-medium text-emerald-800">Recent Improvements</h4>
                <ul className="mt-2 space-y-1 text-sm text-emerald-700">
                  <li>• Updated FAQ collection (+5% success rate)</li>
                  <li>• Enhanced form assistance guides</li>
                  <li>• Improved intent recognition accuracy</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
