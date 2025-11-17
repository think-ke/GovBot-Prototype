// @/lib/analytics-api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchAnalytics<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
  const url = new URL(`${API_BASE_URL}/analytics${endpoint}`)
  if (params) {
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))
  }

  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  })

  if (!response.ok) {
    const err = await response.text().catch(() => '')
    throw new Error(`API Error: ${response.status} ${err}`)
  }

  return response.json()
}

// ================================
// === SHARED TYPES (Merged) ===
// ================================

// IntentAnalysis – used in Executive & Conversation dashboards
export interface IntentAnalysis {
  intent: string
  frequency: number
  containment_rate?: number     // Executive
  avg_duration?: number         // Conversation
  success_rate?: number         // Document
  average_turns?: number        // Legacy fallback
}

// User & Demographics
export interface UserDemographics {
  total_users: number
  user_growth_rate: number
  new_users: number
  active_users: number
  returning_users: number
}

export interface SessionFrequency {
  user_id: string
  total_sessions: number
}

export interface UserSentiment {
  satisfaction_score: number
  positive_conversations: number
  neutral_conversations: number
  negative_conversations: number
  escalation_rate: number
}

export interface RetentionData {
  day_1_retention: number
  day_7_retention: number
  day_30_retention: number
}

// Usage & Traffic
export interface TrafficMetrics {
  total_sessions: number
  total_messages: number
  unique_users: number
}

export interface SessionDuration {
  average_duration_minutes: number
  median_duration_minutes: number
}

export interface PeakHour {
  hour: string
  sessions: number
  messages: number
}

// System Health
export interface SystemHealth {
  uptime_percentage: number
  api_response_time_p50: number
  api_response_time_p95: number
  api_response_time_p99: number
  error_rate: number
}

export interface ErrorEvent {
  timestamp: string
  error_type: string
  count: number
}

// Executive Dashboard
export interface ExecutiveDashboardData {
  containment_rate: number
  total_conversations: number
  automated_conversations: number
  avg_satisfaction_score: number
}

export interface ContainmentRate {
  rate: number
}

// Conversation Analytics
export interface ConversationFlow {
  step: string
  visits: number
  dropoff_rate: number
}

export interface DocumentRetrieval {
  document_id: string
  title: string
  retrieval_count: number
  success_rate: number
}

export interface DropOffData {
  step: string
  dropoffs: number
  total_visits: number
}

export interface SentimentTrends {
  date: string
  positive: number
  neutral: number
  negative: number
}

export interface KnowledgeGaps {
  query: string
  frequency: number
  suggested_intent?: string
}

// ================================
// === FETCH FUNCTIONS (All Unique) ===
// ================================

// User Analytics
export const fetchUserDemographics = (): Promise<UserDemographics> =>
  fetchAnalytics<UserDemographics>('/users/demographics')

export const fetchSessionFrequency = (): Promise<SessionFrequency[]> =>
  fetchAnalytics<SessionFrequency[]>('/users/session-frequency')

export const fetchUserSentiment = (): Promise<UserSentiment> =>
  fetchAnalytics<UserSentiment>('/users/sentiment')

export const fetchUserRetention = (): Promise<RetentionData> =>
  fetchAnalytics<RetentionData>('/users/retention')

// Usage & Traffic
export const fetchTrafficMetrics = (): Promise<TrafficMetrics> =>
  fetchAnalytics<TrafficMetrics>('/traffic')

export const fetchSessionDuration = (): Promise<SessionDuration> =>
  fetchAnalytics<SessionDuration>('/sessions/duration')

export const fetchPeakHours = (days: number = 7): Promise<PeakHour[]> =>
  fetchAnalytics<PeakHour[]>('/traffic/peak-hours', { days })

// System Health
export const fetchSystemHealth = (): Promise<SystemHealth> =>
  fetchAnalytics<SystemHealth>('/system-health')

export const fetchErrorAnalysis = (hours: number = 24): Promise<ErrorEvent[]> =>
  fetchAnalytics<ErrorEvent[]>('/errors', { hours })

// Executive Dashboard
export const fetchExecutiveDashboard = (): Promise<ExecutiveDashboardData> =>
  fetchAnalytics<ExecutiveDashboardData>('/executive')

export const fetchContainmentRate = (): Promise<ContainmentRate> =>
  fetchAnalytics<ContainmentRate>('/containment')

// Conversation Analytics
export const fetchConversationFlows = (): Promise<ConversationFlow[]> =>
  fetchAnalytics<ConversationFlow[]>('/conversation-flows')

export const fetchDocumentRetrieval = (): Promise<DocumentRetrieval[]> =>
  fetchAnalytics<DocumentRetrieval[]>('/documents')

export const fetchDropOffs = (): Promise<DropOffData[]> =>
  fetchAnalytics<DropOffData[]>('/dropoffs')

export const fetchSentimentTrends = (): Promise<SentimentTrends[]> =>
  fetchAnalytics<SentimentTrends[]>('/sentiment')

export const fetchKnowledgeGaps = (): Promise<KnowledgeGaps[]> =>
  fetchAnalytics<KnowledgeGaps[]>('/knowledge-gaps')

// === SHARED: Intent Analysis (used in Executive + Conversation) ===
export const fetchIntentAnalysis = (): Promise<IntentAnalysis[]> =>
  fetchAnalytics<IntentAnalysis[]>('/intents')