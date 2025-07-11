"use client"

import { useState } from 'react'

export function DocumentManager() {
  const [documents, setDocuments] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [collectionId, setCollectionId] = useState('')

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return
    
    if (!collectionId.trim()) {
      alert('Collection ID is required')
      return
    }

    setIsUploading(true)
    
    try {
      // Here you would implement the actual upload logic with the required collection ID
      // For now, just simulate the upload
      await new Promise(resolve => setTimeout(resolve, 1000))
      console.log('Files uploaded:', files, 'Collection ID:', collectionId)
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6">
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
              {isUploading ? 'Uploading...' : 'Upload Documents'}
            </span>
          </label>
        </div>
      </div>

      {/* Collection ID input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Collection ID</label>
        <input
          type="text"
          value={collectionId}
          onChange={(e) => setCollectionId(e.target.value)}
          placeholder="Enter collection ID"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
        <p className="text-xs text-red-500 mt-1">* Required for document organization</p>
      </div>

      {/* Collection ID input */}
      <div className="rounded-lg border bg-card p-6 mb-4">
        <h3 className="text-lg font-semibold mb-4">Document Collection</h3>
        <div>
          <label className="block text-sm font-medium mb-2">Collection ID</label>
          <input
            type="text"
            value={collectionId}
            onChange={(e) => setCollectionId(e.target.value)}
            placeholder="Enter collection ID"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            disabled={isUploading}
          />
          <p className="text-xs text-red-500 mt-1">* Required for organizing documents</p>
        </div>
      </div>

      {/* Upload area */}
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
            <p className="text-sm font-medium text-red-500">Collection ID is required before upload</p>
          </div>
          <div className="flex justify-center space-x-4 text-xs text-muted-foreground">
            <span>PDF</span>
            <span>DOCX</span>
            <span>TXT</span>
            <span>MD</span>
          </div>
        </div>
      </div>

      {/* Documents list */}
      <div className="rounded-lg border bg-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Documents</h3>
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No documents uploaded yet</p>
              <p className="text-sm text-muted-foreground">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                      <span className="text-blue-600 text-sm">📄</span>
                    </div>
                    <div>
                      <p className="font-medium">{doc.name}</p>
                      <p className="text-sm text-muted-foreground">{doc.size} • {doc.type}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="text-sm text-blue-600 hover:text-blue-700">View</button>
                    <button className="text-sm text-red-600 hover:text-red-700">Delete</button>
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
