import { MetricCard } from "@/components/metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, FileText, Target, TrendingDown, Brain, Search, Users, CheckCircle, Loader2 } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, LineChart, Line } from "recharts"
import { useEffect, useState } from "react"
import {
  IntentAnalysis,
  ConversationFlow,
  DocumentRetrieval,
  DropOffData,
  SentimentTrends,
  KnowledgeGaps,
  fetchConversationFlows,
  fetchIntentAnalysis,
  fetchDocumentRetrieval,
  fetchDropOffs,
  fetchSentimentTrends,
  fetchKnowledgeGaps
} from "@/lib/analytics-api"

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
  // State for API data
  const [conversationFlows, setConversationFlows] = useState<ConversationFlow[]>([])
  const [intentData, setIntentData] = useState<IntentAnalysis[]>([])
  const [documentData, setDocumentData] = useState<DocumentRetrieval[]>([])
  const [dropOffData, setDropOffData] = useState<DropOffData | null>(null)
  const [sentimentData, setSentimentData] = useState<SentimentTrends | null>(null)
  const [knowledgeGaps, setKnowledgeGaps] = useState<KnowledgeGaps | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Processed data for charts
  const [processedSentimentTrends, setProcessedSentimentTrends] = useState<any[]>([])
  const [processedDropOffPoints, setProcessedDropOffPoints] = useState<any[]>([])

  // Fetch data on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const [flowsData, intentsData, documentsData, dropOffsData, sentimentTrendsData, knowledgeGapsData] = await Promise.all([
          fetchConversationFlows(),
          fetchIntentAnalysis(),
          fetchDocumentRetrieval(),
          fetchDropOffs(),
          fetchSentimentTrends(),
          fetchKnowledgeGaps()
        ])

        setConversationFlows(flowsData)
        setIntentData(intentsData)
        setDocumentData(documentsData)
        setDropOffData(dropOffsData)
        setSentimentData(sentimentTrendsData)
        setKnowledgeGaps(knowledgeGapsData)

        // Process sentiment data for charts (simulate weekly data)
        if (sentimentTrendsData) {
          const weeklyData = [
            { time: "Week 1", positive: sentimentTrendsData.sentiment_distribution.positive, neutral: sentimentTrendsData.sentiment_distribution.neutral, negative: sentimentTrendsData.sentiment_distribution.negative },
            { time: "Week 2", positive: sentimentTrendsData.sentiment_distribution.positive + 2, neutral: sentimentTrendsData.sentiment_distribution.neutral - 1, negative: sentimentTrendsData.sentiment_distribution.negative - 1 },
            { time: "Week 3", positive: sentimentTrendsData.sentiment_distribution.positive + 1, neutral: sentimentTrendsData.sentiment_distribution.neutral, negative: sentimentTrendsData.sentiment_distribution.negative - 1 },
            { time: "Week 4", positive: sentimentTrendsData.sentiment_distribution.positive, neutral: sentimentTrendsData.sentiment_distribution.neutral + 1, negative: sentimentTrendsData.sentiment_distribution.negative },
          ]
          setProcessedSentimentTrends(weeklyData)
        }

        // Process drop-off data
        if (dropOffsData) {
          const totalUsers = 1000 // Simulated base
          const processedDropOffs = [
            { stage: "Initial Query", users: totalUsers, percentage: 100 },
            { stage: "First Response", users: Math.round(totalUsers * 0.95), percentage: 95 },
            { stage: "Follow-up", users: Math.round(totalUsers * 0.82), percentage: 82 },
            { stage: "Document Access", users: Math.round(totalUsers * 0.68), percentage: 68 },
            { stage: "Resolution", users: Math.round(totalUsers * 0.58), percentage: 58 },
          ]
          setProcessedDropOffPoints(processedDropOffs)
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
        <span className="ml-2">Loading conversation analytics...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading conversation analytics</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  // Calculate metrics from real data
  const avgTurns = conversationFlows.length > 0 
    ? (conversationFlows.reduce((sum, flow) => sum + flow.turn_number, 0) / conversationFlows.length).toFixed(1)
    : "0.0"
  
  const avgDocumentSuccess = documentData.length > 0
    ? (documentData.reduce((sum, doc) => sum + doc.success_rate, 0) / documentData.length).toFixed(1)
    : "0.0"

  const avgIntentSuccess = intentData.length > 0
    ? (intentData.reduce((sum, intent) => sum + intent.success_rate, 0) / intentData.length).toFixed(1)
    : "0.0"

  const avgDropOff = dropOffData?.drop_off_points.length > 0
    ? (dropOffData.drop_off_points.reduce((sum, point) => sum + point.abandonment_rate, 0) / dropOffData.drop_off_points.length).toFixed(1)
    : "0.0"

  return (
    <div className="space-y-6">
      {/* Conversation Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Avg Turns per Conversation"
          value={avgTurns}
          change={0} // Would need historical data for change calculation
          changeLabel="vs last month"
          icon={<MessageSquare className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Document Retrieval Success"
          value={`${avgDocumentSuccess}%`}
          change={0} // Would need historical data for change calculation
          changeLabel="vs last month"
          icon={<FileText className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Intent Recognition Rate"
          value={`${avgIntentSuccess}%`}
          change={0} // Would need historical data for change calculation
          changeLabel="vs last month"
          icon={<Target className="w-4 h-4" />}
          trend="neutral"
        />
        <MetricCard
          title="Conversation Drop-off"
          value={`${avgDropOff}%`}
          change={0} // Would need historical data for change calculation
          changeLabel="vs last month"
          icon={<TrendingDown className="w-4 h-4" />}
          trend="neutral"
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
              <LineChart data={conversationFlows}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="turn_number" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="completion_rate"
                  stroke="var(--color-completionRate)"
                  strokeWidth={3}
                  dot={{ fill: "var(--color-completionRate)", strokeWidth: 2, r: 4 }}
                  name="Completion Rate (%)"
                />
                <Line
                  type="monotone"
                  dataKey="abandonment_rate"
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
              {intentData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.intent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{item.frequency} queries</Badge>
                      <Badge
                        className={
                          item.success_rate > 90
                            ? "bg-emerald-100 text-emerald-800"
                            : item.success_rate > 80
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }
                      >
                        {item.success_rate.toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${intentData.length > 0 ? (item.frequency / Math.max(...intentData.map(i => i.frequency))) * 100 : 0}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Avg turns: {item.average_turns.toFixed(1)}</span>
                    <span>Success: {item.success_rate.toFixed(1)}%</span>
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
                <BarChart data={documentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="document_type" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="access_frequency" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Access Frequency" />
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
                <BarChart data={processedSentimentTrends}>
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
              {processedDropOffPoints.map((stage, index) => (
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
                  {index < processedDropOffPoints.length - 1 && (
                    <div className="text-xs text-red-600 ml-2">
                      Drop-off: {processedDropOffPoints[index].users - processedDropOffPoints[index + 1].users} users
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
                  <div className="text-2xl font-bold text-emerald-600">{avgDocumentSuccess}%</div>
                  <div className="text-sm text-emerald-700">Retrieval Success</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {conversationFlows.length > 0 
                      ? (conversationFlows.reduce((sum, flow) => sum + flow.average_response_time, 0) / conversationFlows.length).toFixed(1)
                      : '0.0'
                    }s
                  </div>
                  <div className="text-sm text-blue-700">Avg Response Time</div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Top Performing Document Types</h4>
                {documentData.slice(0, 3).map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">{item.document_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <div className="flex items-center space-x-2">
                      <Badge className="bg-emerald-100 text-emerald-800">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        {item.success_rate.toFixed(1)}%
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
                  {knowledgeGaps?.knowledge_gaps.slice(0, 3).map((gap, index) => (
                    <li key={index}>• {gap.topic.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} ({gap.success_rate * 100}% success rate)</li>
                  )) || <li>• No significant knowledge gaps identified</li>}
                </ul>
              </div>

              <div className="p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                <h4 className="font-medium text-blue-800">Recommended Actions</h4>
                <ul className="mt-2 space-y-1 text-sm text-blue-700">
                  {knowledgeGaps?.recommendations.slice(0, 3).map((recommendation, index) => (
                    <li key={index}>• {recommendation}</li>
                  )) || <li>• Continue monitoring conversation performance</li>}
                </ul>
              </div>

              <div className="p-3 bg-emerald-50 border-l-4 border-emerald-400 rounded">
                <h4 className="font-medium text-emerald-800">System Performance</h4>
                <ul className="mt-2 space-y-1 text-sm text-emerald-700">
                  <li>• Average intent recognition: {avgIntentSuccess}%</li>
                  <li>• Document retrieval success: {avgDocumentSuccess}%</li>
                  <li>• {sentimentData ? Math.round(sentimentData.sentiment_distribution.positive) : 0}% positive sentiment</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
