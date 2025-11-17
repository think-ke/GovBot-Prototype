"use client"

import { useState, useEffect } from "react"
import { Agency, CreateAgencyRequest } from "@/lib/types"
import { apiClient } from "@/lib/api-client"

export function AgencyManager() {
  const [agencies, setAgencies] = useState<Agency[]>([])
  const [newAgencyName, setNewAgencyName] = useState("")
  const [newAgencyDescription, setNewAgencyDescription] = useState("")
  const [newAgencyType, setNewAgencyType] = useState<"documents" | "webpages" | "mixed">("mixed")
  const [isCreating, setIsCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string>("")

  useEffect(() => {
    loadAgencies()
  }, [])

  const loadAgencies = async () => {
    setLoading(true)
    setError(null)
    try {
      const agenciesData = await apiClient.getCollections()
      setAgencies(
        agenciesData.map((a: any) => ({
          id: a.id,
          name: a.name,
          description: a.description ?? "",
          type: a.type ?? "mixed",
          document_count: a.document_count ?? 0,
          webpage_count: a.webpage_count ?? 0,
          created_at: a.created_at ?? new Date().toISOString(),
          updated_at: a.updated_at ?? new Date().toISOString(),
        }))
      )
    } catch (error) {
      console.error("Failed to load agencies:", error)
      setError("Failed to load agencies. Please refresh the page.")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgency = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!newAgencyName.trim()) {
      setError("Agency name is required")
      return
    }

    setIsCreating(true)
    setError(null)
    setDebugInfo("Starting creation...")
    
    try {
      const agencyRequest: CreateAgencyRequest = {
        name: newAgencyName.trim(),
        description: newAgencyDescription.trim() || undefined,
        type: newAgencyType,
      }

      console.log("🚀 Creating agency with:", agencyRequest)
      setDebugInfo("Sending request to API...")

      // Add timeout wrapper
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error("Request timeout after 30 seconds")), 30000)
      })

      const createPromise = apiClient.createCollection(agencyRequest)

      console.log("⏳ Waiting for API response...")
      setDebugInfo("Waiting for server response...")

      const newAgency = await Promise.race([createPromise, timeoutPromise]) as any

      console.log("✅ Agency created successfully:", newAgency)
      setDebugInfo("Agency created! Updating list...")

      // Verify we got a valid response
      if (!newAgency || !newAgency.id) {
        throw new Error("Invalid response from server - missing agency ID")
      }

      setAgencies((prev) => [
        {
          id: newAgency.id,
          name: newAgency.name || newAgencyName,
          description: newAgency.description ?? newAgencyDescription,
          type: newAgency.type ?? newAgencyType,
          document_count: newAgency.document_count ?? 0,
          webpage_count: newAgency.webpage_count ?? 0,
          created_at: newAgency.created_at ?? new Date().toISOString(),
          updated_at: newAgency.updated_at ?? new Date().toISOString(),
        },
        ...prev,
      ])

      // Reset form
      setNewAgencyName("")
      setNewAgencyDescription("")
      setNewAgencyType("mixed")
      setShowCreateForm(false)
      setDebugInfo("Success! Agency created.")
      
      // Clear debug info after success
      setTimeout(() => setDebugInfo(""), 3000)
    } catch (error: any) {
      console.error("❌ Agency creation failed:", error)
      
      // Detailed error logging
      console.log("Error type:", typeof error)
      console.log("Error name:", error?.name)
      console.log("Error message:", error?.message)
      console.log("Error stack:", error?.stack)
      console.log("Full error object:", error)
      
      let errorMessage = "Failed to create agency. "
      
      if (error.message === "Request timeout after 30 seconds") {
        errorMessage += "The request took too long. Please check your network connection and try again."
        setDebugInfo("Timeout - server not responding")
      } else if (error.response) {
        // HTTP error response
        const status = error.response.status
        const data = error.response.data
        errorMessage += `Server error (${status}): ${data?.message || data?.error || error.response.statusText || "Unknown error"}`
        setDebugInfo(`Server returned ${status} error`)
      } else if (error.request) {
        // Network error
        errorMessage += "Network error. Cannot reach the server. Check your connection and API endpoint."
        setDebugInfo("Network error - cannot reach server")
      } else if (error.message) {
        // Other error
        errorMessage += error.message
        setDebugInfo(`Error: ${error.message}`)
      } else {
        errorMessage += "Unknown error occurred. Check console for details."
        setDebugInfo("Unknown error")
      }
      
      setError(errorMessage)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteAgency = async (agencyId: string) => {
    if (!confirm("Are you sure you want to delete this agency? This action cannot be undone.")) return

    setError(null)
    try {
      await apiClient.deleteCollection(agencyId)
      setAgencies((prev) => prev.filter((a) => a.id !== agencyId))
    } catch (error: any) {
      console.error("Failed to delete agency:", error)
      setError(`Failed to delete agency: ${error.message || "Unknown error"}`)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Agency Management</h1>
          <p className="text-muted-foreground">
            Manage your agency documents and webpages
          </p>
        </div>
        <button
          onClick={() => {
            setShowCreateForm(!showCreateForm)
            setError(null)
            setDebugInfo("")
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          {showCreateForm ? "Cancel" : "Create Agency"}
        </button>
      </div>

      {/* Debug info */}
      {debugInfo && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center">
            <span className="text-blue-600 mr-2">ℹ️</span>
            <p className="text-sm text-blue-800">{debugInfo}</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <div className="flex items-start">
            <span className="text-red-600 mr-2">⚠️</span>
            <div className="flex-1">
              <p className="text-sm text-red-800">{error}</p>
              <p className="text-xs text-red-600 mt-1">Check browser console (F12) for more details</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Create agency form */}
      {showCreateForm && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Agency</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Agency Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={newAgencyName}
                onChange={(e) => {
                  setNewAgencyName(e.target.value)
                  setError(null)
                }}
                placeholder="Enter agency name"
                disabled={isCreating}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Description (Optional)
              </label>
              <textarea
                value={newAgencyDescription}
                onChange={(e) => setNewAgencyDescription(e.target.value)}
                placeholder="Enter agency description"
                rows={3}
                disabled={isCreating}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Agency Type</label>
              <select
                value={newAgencyType}
                onChange={(e) =>
                  setNewAgencyType(
                    e.target.value as "documents" | "webpages" | "mixed"
                  )
                }
                disabled={isCreating}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              >
                <option value="mixed">Mixed (Documents & Webpages)</option>
                <option value="documents">Documents Only</option>
                <option value="webpages">Webpages Only</option>
              </select>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={handleCreateAgency}
                disabled={isCreating || !newAgencyName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isCreating && (
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {isCreating ? "Creating..." : "Create Agency"}
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false)
                  setError(null)
                  setDebugInfo("")
                }}
                disabled={isCreating}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agencies grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading Agencies...</p>
          </div>
        ) : agencies.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">🏢</span>
            </div>
            <p className="text-muted-foreground mb-2">
              No agencies created yet
            </p>
            <p className="text-sm text-muted-foreground">
              Create your first agency to get started
            </p>
          </div>
        ) : (
          agencies.map((agency) => (
            <div
              key={agency.id}
              className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">{agency.name}</h3>
                  {agency.description && (
                    <p className="text-sm text-muted-foreground mb-2">
                      {agency.description}
                    </p>
                  )}
                  <div className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md mb-2">
                    {agency.type}
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <span>{agency.document_count ?? 0} documents</span>
                    <span>{agency.webpage_count ?? 0} webpages</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="text-sm text-blue-600 hover:text-blue-700">
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteAgency(agency.id)}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Agency ID</span>
                  <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                    {agency.id}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Created</span>
                  <span className="font-medium">
                    {new Date(agency.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Updated</span>
                  <span className="font-medium">
                    {new Date(agency.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center space-x-2">
                  <button className="flex-1 text-sm text-center py-2 px-3 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100">
                    View Contents
                  </button>
                  <button className="flex-1 text-sm text-center py-2 px-3 border border-gray-300 rounded-md hover:bg-gray-50">
                    Add Content
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}