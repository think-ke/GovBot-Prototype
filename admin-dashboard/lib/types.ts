export interface DashboardStats {
  total_documents: number
  total_webpages: number
  total_agencies: number
  active_users: number
  recent_uploads: number
  total_collections: number
  total_storage_size: number
  data_storage_size: number
}

export interface Document {
  id: string
  name: string
  size: number
  type: string
  uploaded_at: string
  collection_id: string
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down'
  uptime: number
  last_check: string
}

export interface Agency {
  id: string
  name: string
  description?: string
  type: 'documents' | 'webpages' | 'mixed'
  document_count: number
  webpage_count: number
  created_at: string
  updated_at: string
}

export interface CreateAgencyRequest {
  name: string
  description?: string
  type: 'documents' | 'webpages' | 'mixed'
}

export interface IntentAnalysis {
  intent: string
  frequency: number
  success_rate: number
  average_turns: number
}

export interface ConversationFlow {
  turn_number: number
  completion_rate: number
}

export interface DocumentRetrieval {
  document_type: string
  access_frequency: number
  success_rate: number
}

export interface DropOffData {
  drop_off_points: Array<{
    turn: number
    abandonment_rate: number
  }>
  common_triggers: string[]
}

export interface SentimentTrends {
  sentiment_distribution: {
    positive: number
    neutral: number
    negative: number
  }
}

export interface KnowledgeGaps {
  knowledge_gaps: Array<{
    topic: string
    query_frequency: number
    success_rate: number
    example_queries: string[]
  }>
  recommendations: string[]
}