"use client"

import { MetricCard } from "./metric-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, FileText, Target, TrendingDown, Brain, Search, CheckCircle, Loader2 } from "lucide-react"
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

// ------------------------------------------------------------------
// Mock / Fallback Data
// ------------------------------------------------------------------
const mockIntents = [
  { intent: "document_request", frequency: 485, containment_rate: 94.2, avg_duration: 2.8 },
  { intent: "general_inquiry", frequency: 320, containment_rate: 88.5, avg_duration: 3.2 },
  { intent: "form_assistance", frequency: 280, containment_rate: 91.8, avg_duration: 4.1 },
  { intent: "status_check", frequency: 245, containment_rate: 96.1, avg_duration: 2.1 },
  { intent: "complaint_handling", frequency: 180, containment_rate: 76.3, avg_duration: 5.2 },
]

const mockDocuments = [
  { document_id: "1", title: "Forms & Applications", retrieval_count: 342, success_rate: 94.2 },
  { document_id: "2", title: "Policy Documents", retrieval_count: 285, success_rate: 91.8 },
  { document_id: "3", title: "Service Guidelines", retrieval_count: 220, success_rate: 88.5 },
  { document_id: "4", title: "FAQ Responses", retrieval_count: 195, success_rate: 96.1 },
  { document_id: "5", title: "Legal Documents", retrieval_count: 145, success_rate: 85.2 },
]

const mockDropOffs = [
  { step: "Initial Query", dropoffs: 50, total_visits: 1000 },
  { step: "First Response", dropoffs: 70, total_visits: 950 },
  { step: "Follow-up", dropoffs: 60, total_visits: 880 },
  { step: "Resolution", dropoffs: 60, total_visits: 820 },
  { step: "Completion", dropoffs: 60, total_visits: 760 },
]

const mockSentiment = [
  { date: "2025-10-01", positive: 72, neutral: 22, negative: 6 },
  { date: "2025-10-08", positive: 74, neutral: 21, negative: 5 },
  { date: "2025-10-15", positive: 73, neutral: 22, negative: 5 },
  { date: "2025-10-22", positive: 75, neutral: 20, negative: 5 },
]

const mockKnowledgeGaps = [
  { query: "How to apply for digital ID?", frequency: 45, suggested_intent: "document_request" },
  { query: "Appeal rejected application", frequency: 32, suggested_intent: "appeal_process" },
  { query: "Emergency contact numbers", frequency: 28, suggested_intent: "emergency_services" },
  { query: "Can I pay online?", frequency: 24, suggested_intent: "payment_methods" },
]

export function ConversationAnalyticsDashboard() {
  const [conversationFlows, setConversationFlows] = useState<ConversationFlow[]>([])
  const [intentData, setIntentData] = useState<IntentAnalysis[]>([])
  const [documentData, setDocumentData] = useState<DocumentRetrieval[]>([])
  const [dropOffData, setDropOffData] = useState<DropOffData[]>([])
  const [sentimentData, setSentimentData] = useState<SentimentTrends[]>([])
  const [knowledgeGaps, setKnowledgeGaps] = useState<KnowledgeGaps[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [processedDropOffs, setProcessedDropOffs] = useState<any[]>([])
  const [processedSentiment, setProcessedSentiment] = useState<any[]>([])

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true)
        setError(null)

        const [
          flows,
          intents,
          docs,
          dropoffs,
          sentiment,
          gaps
        ] = await Promise.all([
          fetchConversationFlows().catch(() => []),
          fetchIntentAnalysis().catch(() => []),
          fetchDocumentRetrieval().catch(() => []),
          fetchDropOffs().catch(() => []),
          fetchSentimentTrends().catch(() => []),
          fetchKnowledgeGaps().catch(() => [])
        ])

        const finalIntents = intents.length ? intents : mockIntents
        const finalDocs = docs.length ? docs : mockDocuments
        const finalDropoffs = dropoffs.length ? dropoffs : mockDropOffs
        const finalSentiment = sentiment.length ? sentiment : mockSentiment
        const finalGaps = gaps.length ? gaps : mockKnowledgeGaps

        setConversationFlows(flows)
        setIntentData(finalIntents)
        setDocumentData(finalDocs)
        setDropOffData(finalDropoffs)
        setSentimentData(finalSentiment)
        setKnowledgeGaps(finalGaps)

        // === Process Drop-offs (Cumulative) ===
        const startVisits = finalDropoffs[0]?.total_visits ?? 1000
        let cumulative = startVisits
        const dropoffPoints = finalDropoffs.map((d, i) => {
          const remaining = d.total_visits - d.dropoffs
          const percentage = Math.round((remaining / startVisits) * 100)
          if (i > 0) cumulative = remaining
          return { stage: d.step, users: remaining, percentage }
        })
        setProcessedDropOffs(dropoffPoints)

        // === Process Sentiment (Weekly) ===
        const weekly = finalSentiment.map((s, i) => ({
          week: `Week ${i + 1}`,
          positive: s.positive,
          neutral: s.neutral,
          negative: s.negative
        }))
        setProcessedSentiment(weekly)

      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data")
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
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
      <div className="flex items-center justify-center h-64 text-center">
        <p className="text-red-600 mb-2">Error loading conversation analytics</p>
        <p className="text-sm text-gray-600">{error}</p>
      </div>
    )
  }

  // === KPI Calculations ===
  const totalConversations = intentData.reduce((s, i) => s + i.frequency, 0)

  const avgTurns = conversationFlows.length > 0
    ? conversationFlows.reduce((sum, f) => {
        const turnMatch = f.step.match(/(\d+)/)
        const turn = turnMatch ? parseInt(turnMatch[1], 10) : 1
        return sum + turn
      }, 0) / conversationFlows.length
    : 3.2

  const completionRate = conversationFlows.length > 0
    ? (conversationFlows.reduce((s, f) => s + (100 - f.dropoff_rate), 0) / conversationFlows.length).toFixed(1)
    : "82.4"

  const docSuccessRate = documentData.length > 0
    ? (documentData.reduce((s, d) => s + d.success_rate, 0) / documentData.length).toFixed(1)
    : "91.2"

  const maxFreq = intentData[0]?.frequency || 1

  return (
    <div className="space-y-6">

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Conversations" value={totalConversations} change={0} icon={<MessageSquare className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Avg. Turns" value={avgTurns.toFixed(1)} change={0} icon={<Target className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Completion Rate" value={`${completionRate}%`} change={0} icon={<CheckCircle className="w-4 h-4" />} trend="neutral" />
        <MetricCard title="Doc Retrieval Success" value={`${docSuccessRate}%`} change={0} icon={<FileText className="w-4 h-4" />} trend="neutral" />
      </div>

      {/* Intents + Flow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" /> Top Intents
            </CardTitle>
          </CardHeader>
          <CardContent>
            {intentData.slice(0, 5).map((intent, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg mb-3">
                <div className="flex justify-between mb-1">
                  <span className="font-medium capitalize">{intent.intent.replace(/_/g, " ")}</span>
                  <div className="flex gap-2">
                    <Badge variant="secondary">{intent.frequency}</Badge>
                    <Badge
                      className={
                        (intent.containment_rate ?? 0) > 90
                          ? "bg-emerald-100 text-emerald-800"
                          : (intent.containment_rate ?? 0) > 80
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                      }
                    >
                      {(intent.containment_rate ?? 0).toFixed(1)}%
                    </Badge>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${(intent.frequency / maxFreq) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Avg {(intent.avg_duration ?? 0).toFixed(1)} turns
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Conversation Flow</CardTitle></CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={conversationFlows.map((f, i) => ({
                    turn: `Turn ${i + 1}`,
                    completion: 100 - f.dropoff_rate,
                    abandonment: f.dropoff_rate
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="turn" />
                  <YAxis />
                  <Line type="monotone" dataKey="completion" stroke="#10b981" strokeWidth={2} name="Completion" />
                  <Line type="monotone" dataKey="abandonment" stroke="#ef4444" strokeWidth={2} name="Abandonment" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sentiment + Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Sentiment Trends</CardTitle></CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={processedSentiment}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Bar dataKey="positive" stackId="a" fill="#10b981" />
                  <Bar dataKey="neutral" stackId="a" fill="#f59e0b" />
                  <Bar dataKey="negative" stackId="a" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex justify-center gap-6 text-sm">
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-emerald-500 rounded-full" /> Positive</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-yellow-500 rounded-full" /> Neutral</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-red-500 rounded-full" /> Negative</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" /> Document Retrieval
            </CardTitle>
          </CardHeader>
          <CardContent>
            {documentData.slice(0, 6).map((doc, i) => (
              <div key={i} className="mb-3">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{doc.title}</span>
                  <div className="flex gap-2">
                    <span className="text-sm text-gray-600">{doc.retrieval_count}</span>
                    <Badge
                      className={
                        doc.success_rate > 95
                          ? "bg-emerald-100 text-emerald-800"
                          : doc.success_rate > 90
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                      }
                    >
                      {doc.success_rate.toFixed(1)}%
                    </Badge>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${doc.success_rate}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Knowledge Gaps + Drop-offs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" /> Knowledge Gaps
            </CardTitle>
          </CardHeader>
          <CardContent>
            {knowledgeGaps.slice(0, 4).map((gap, i) => (
              <div key={i} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200 mb-3">
                <div className="flex justify-between mb-1">
                  <h4 className="font-medium text-yellow-800">"{gap.query}"</h4>
                  <Badge variant="secondary">{gap.frequency}</Badge>
                </div>
                {gap.suggested_intent && (
                  <p className="text-xs text-gray-600">
                    Suggested: {gap.suggested_intent.replace(/_/g, " ")}
                  </p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="w-5 h-5" /> Drop-off Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            {processedDropOffs.map((p, i) => (
              <div key={i} className="mb-3">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">{p.stage}</span>
                  <div className="flex gap-2">
                    <span className="text-sm text-gray-600">{p.users} users</span>
                    <Badge variant="secondary">{p.percentage}%</Badge>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${p.percentage}%` }} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

    </div>
  )
}