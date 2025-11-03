import { DashboardStats, SystemHealth, Document, Agency, CreateAgencyRequest } from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ""

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(message)
    this.name = "APIError"
  }
}

const fetchWithAuth = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": `${API_KEY}`,
        ...(options.headers || {}),
      },
    })

    let data: any
    const contentType = response.headers.get("content-type")
    
    if (contentType && contentType.includes("application/json")) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    if (!response.ok) {
      const errorMessage = data?.detail || data?.message || data || response.statusText
      throw new APIError(
        errorMessage,
        response.status,
        response.statusText,
        data
      )
    }

    return data as T
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new APIError(
        "Network error: Unable to connect to the server",
        0,
        "Network Error"
      )
    }
    
    throw error
  }
}

export const apiClient = {
  // Dashboard
  getDashboardStats: () => fetchWithAuth<DashboardStats>("/dashboard/stats"),
  getSystemHealth: () => fetchWithAuth<SystemHealth>("/system/health"),

  // Documents
  getDocuments: (params?: { limit?: number }) =>
    fetchWithAuth<Document[]>(`/documents?limit=${params?.limit || 10}`),

  getDocumentsByCollection: (collectionId: string, params?: { limit?: number }) =>
    fetchWithAuth<Document[]>(`/documents/collection/${collectionId}`),

  uploadDocument: async (file: File, metadata: any) => {
    try {
      const formData = new FormData()
      formData.append("file", file)
      
      // Append metadata fields individually instead of as JSON string
      if (metadata.collection_id) {
        formData.append("collection_id", metadata.collection_id)
      }
      if (metadata.description) {
        formData.append("description", metadata.description)
      }
      if (metadata.is_public !== undefined) {
        formData.append("is_public", String(metadata.is_public))
      }
      
      const response = await fetch(`${API_BASE_URL}/documents/`, {
        method: "POST",
        body: formData,
        headers: {
          "X-API-Key": `${API_KEY}`,
        },
      })

      let data: any
      const contentType = response.headers.get("content-type")
      
      if (contentType && contentType.includes("application/json")) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        const errorMessage = data?.detail || data?.message || data || response.statusText
        throw new APIError(errorMessage, response.status, response.statusText, data)
      }

      return data
    } catch (error) {
      if (error instanceof APIError) {
        throw error
      }
      throw new APIError("Upload failed", 0, "Network Error")
    }
  },

  deleteDocument: (id: number) =>
    fetchWithAuth<void>(`/documents/${id}`, { method: "DELETE" }),

  // Agencies / Collections
  getCollections: () => fetchWithAuth<Agency[]>("/collection-stats/collections"),
  
  createCollection: async (data: CreateAgencyRequest) => {
    console.log("API Client: Creating collection with data:", data)
    try {
      const result = await fetchWithAuth<Agency>("/collection-stats/", {
        method: "POST",
        body: JSON.stringify(data),
      })
      console.log("API Client: Collection created successfully:", result)
      return result
    } catch (error) {
      console.error("API Client: Collection creation failed:", error)
      throw error
    }
  },
  
  deleteCollection: (id: string) =>
    fetchWithAuth<void>(`/collections/${id}`, { method: "DELETE" }),

  // Website Crawl
  createCrawlJob: (data: { url: string; options?: any }) =>
    fetchWithAuth<{ id: string; status: string }>("/websites/crawl", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Analytics
  getAnalytics: () => fetchWithAuth<any>("/analytics"),
}

export { APIError }