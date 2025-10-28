"use client"

import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api-client"

import { Document } from "@/lib/types"


export interface Collection {
  id: string
  name: string
  document_count: number
}

export function DocumentManager() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [collectionId, setCollectionId] = useState("")
  const [collections, setCollections] = useState<Collection[]>([])
  const [selectedCollection, setSelectedCollection] = useState("")
  const [loading, setLoading] = useState(false)

  // 🔹 Load collections on component mount
  useEffect(() => {
    loadCollections()
  }, [])

  // 🔹 Load documents when collection changes
  useEffect(() => {
    if (selectedCollection) {
      loadDocumentsByCollection(selectedCollection)
    } else {
      loadAllDocuments()
    }
  }, [selectedCollection])

  // 🔹 Load all collections
  const loadCollections = async () => {
    try {
      const collectionsData = await apiClient.getCollections()
      setCollections(collectionsData || [])
    } catch (error) {
      console.error("Failed to load collections:", error)
    }
  }

  // 🔹 Load all documents
  const loadAllDocuments = async () => {
    setLoading(true)
    try {
      
    } catch (error) {
      console.error("Failed to load documents:", error)
    } finally {
      setLoading(false)
    }
  }

  // 🔹 Load documents by collection
  const loadDocumentsByCollection = async (collectionId: string) => {
    setLoading(true)
    try {
      const documentsData = await apiClient.getDocumentsByCollection(collectionId, { limit: 100 })
      setDocuments(documentsData || [])
    } catch (error) {
      console.error("Failed to load documents by collection:", error)
    } finally {
      setLoading(false)
    }
  }

  // 🔹 Handle upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    if (!collectionId.trim()) {
      alert("Collection ID is required")
      return
    }

    setIsUploading(true)

    try {
      const uploadPromises = Array.from(files).map((file) =>
        apiClient.uploadDocument(file, {
          collection_id: collectionId,
          description: `Uploaded file: ${file.name}`,
          is_public: false,
        })
      )

      const uploadedDocuments = await Promise.all(uploadPromises)

      // Refresh document list
      if (selectedCollection) {
        await loadDocumentsByCollection(selectedCollection)
      } else {
        await loadAllDocuments()
      }

      console.log("Files uploaded successfully:", uploadedDocuments)
    } catch (error) {
      console.error("Upload failed:", error)
      alert("Upload failed. Please try again.")
    } finally {
      setIsUploading(false)
    }
  }

  // 🔹 Handle delete
  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm("Are you sure you want to delete this document?")) return

    try {
      await apiClient.deleteDocument(documentId)
      // Refresh document list
      if (selectedCollection) {
        await loadDocumentsByCollection(selectedCollection)
      } else {
        await loadAllDocuments()
      }
    } catch (error) {
      console.error("Failed to delete document:", error)
      alert("Failed to delete document. Please try again.")
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Document Management</h1>
          <p className="text-muted-foreground">Upload, organize, and manage your documents</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="cursor-pointer">
            <input
              type="file"
              multiple
              className="sr-only"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            <span className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50">
              {isUploading ? "Uploading..." : "Upload Documents"}
            </span>
          </label>
        </div>
      </div>

      {/* Collection Filter */}
      <div className="mb-4">
        <label htmlFor="collection-filter" className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Collection
        </label>
        <select
          id="collection-filter"
          value={selectedCollection}
          onChange={(e) => setSelectedCollection(e.target.value)}
          className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Collections</option>
          {collections.map((collection) => (
            <option key={collection.id} value={collection.id}>
              {collection.name} ({collection.document_count} documents)
            </option>
          ))}
        </select>
      </div>

      {/* Upload Configuration */}
      <div className="rounded-lg border bg-card p-6 mb-4">
        <h3 className="text-lg font-semibold mb-4">Upload Configuration</h3>
        <div>
          <label className="block text-sm font-medium mb-2">Collection ID for Upload *</label>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              placeholder="Enter collection ID"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={isUploading}
            />
            {collections.length > 0 && (
              <select
                value={collectionId}
                onChange={(e) => setCollectionId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isUploading}
              >
                <option value="">Select existing...</option>
                {collections.map((collection) => (
                  <option key={collection.id} value={collection.id}>
                    {collection.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          <p className="text-xs text-red-500 mt-1">* Required for organizing documents</p>
        </div>
      </div>

      {/* Upload Drop Area */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-xl">📁</span>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium">Drag and drop files here</h3>
            <p className="text-sm text-muted-foreground">or click the button above to browse</p>
            {!collectionId && (
              <p className="text-sm font-medium text-red-500">Collection ID is required before upload</p>
            )}
          </div>
          <div className="flex justify-center space-x-4 text-xs text-muted-foreground">
            <span>PDF</span>
            <span>DOCX</span>
            <span>TXT</span>
            <span>MD</span>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="rounded-lg border bg-card">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              Documents{" "}
              {selectedCollection &&
                `in ${collections.find((c) => c.id === selectedCollection)?.name || selectedCollection}`}
              {documents.length > 0 && ` (${documents.length})`}
            </h3>
            {loading && <div className="text-sm text-muted-foreground">Loading...</div>}
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                {selectedCollection ? "No documents in this collection" : "No documents uploaded yet"}
              </p>
              <p className="text-sm text-muted-foreground">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                      <span className="text-blue-600 text-sm">📄</span>
                    </div>
                    <div>
                      <p className="font-medium">{doc.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(doc.size / 1024).toFixed(2)} KB • Type: {doc.type}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Collection: {doc.collection_id} • Uploaded:{" "}
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => window.open(`/documents/${doc.id}`, "_blank")}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleDeleteDocument(Number(doc.id))}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
