"use client"

import { useState, useEffect } from 'react'
import { Collection, CreateCollectionRequest } from '@/lib/types'
import { apiClient } from '@/lib/api-client'

export function CollectionManager() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [newCollectionName, setNewCollectionName] = useState('')
  const [newCollectionDescription, setNewCollectionDescription] = useState('')
  const [newCollectionType, setNewCollectionType] = useState<'documents' | 'webpages' | 'mixed'>('mixed')
  const [isCreating, setIsCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [loading, setLoading] = useState(false)

  // Load collections on component mount
  useEffect(() => {
    loadCollections()
  }, [])

  const loadCollections = async () => {
    setLoading(true)
    try {
      const collectionsData = await apiClient.getCollections()
      setCollections(collectionsData)
    } catch (error) {
      console.error('Failed to load collections:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCollection = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!newCollectionName.trim()) return

    setIsCreating(true)
    
    try {
      const collectionRequest: CreateCollectionRequest = {
        name: newCollectionName,
        description: newCollectionDescription || undefined,
        type: newCollectionType
      }
      
      const newCollection = await apiClient.createCollection(collectionRequest)
      setCollections(prev => [newCollection, ...prev])
      setNewCollectionName('')
      setNewCollectionDescription('')
      setNewCollectionType('mixed')
      setShowCreateForm(false)
    } catch (error) {
      console.error('Collection creation failed:', error)
      alert('Failed to create collection. Please try again.')
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteCollection = async (collectionId: string) => {
    if (!confirm('Are you sure you want to delete this collection? This action cannot be undone.')) return

    try {
      await apiClient.deleteCollection(collectionId)
      setCollections(prev => prev.filter(c => c.id !== collectionId))
    } catch (error) {
      console.error('Failed to delete collection:', error)
      alert('Failed to delete collection. Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Collection Management</h1>
          <p className="text-muted-foreground">Organize your documents and webpages into collections</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {showCreateForm ? 'Cancel' : 'Create Collection'}
        </button>
      </div>

      {/* Create collection form */}
      {showCreateForm && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Collection</h3>
          <form onSubmit={handleCreateCollection} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Collection Name</label>
              <input
                type="text"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                placeholder="Enter collection name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
                disabled={isCreating}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Description (Optional)</label>
              <textarea
                value={newCollectionDescription}
                onChange={(e) => setNewCollectionDescription(e.target.value)}
                placeholder="Enter collection description"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isCreating}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Collection Type</label>
              <select
                value={newCollectionType}
                onChange={(e) => setNewCollectionType(e.target.value as 'documents' | 'webpages' | 'mixed')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isCreating}
              >
                <option value="mixed">Mixed (Documents & Webpages)</option>
                <option value="documents">Documents Only</option>
                <option value="webpages">Webpages Only</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                type="submit"
                disabled={isCreating || !newCollectionName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create Collection'}
              </button>
              
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Collections grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-12">
            <p className="text-muted-foreground">Loading collections...</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📁</span>
            </div>
            <p className="text-muted-foreground mb-2">No collections yet</p>
            <p className="text-sm text-muted-foreground">Create your first collection to organize your content</p>
          </div>
        ) : (
          collections.map((collection: Collection) => (
            <div key={collection.id} className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">{collection.name}</h3>
                  {collection.description && (
                    <p className="text-sm text-muted-foreground mb-2">{collection.description}</p>
                  )}
                  <div className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md mb-2">
                    {collection.type}
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <span>{collection.document_count} documents</span>
                    <span>{collection.webpage_count} webpages</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={() => {/* TODO: Implement edit functionality */}}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Edit
                  </button>
                  <button 
                    onClick={() => handleDeleteCollection(collection.id)}
                    className="text-sm text-red-600 hover:text-red-700"
                    disabled={collection.id === 'default'}
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Collection ID</span>
                  <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{collection.id}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Created</span>
                  <span className="font-medium">{new Date(collection.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Updated</span>
                  <span className="font-medium">{new Date(collection.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={() => {/* TODO: Navigate to collection view */}}
                    className="flex-1 text-sm text-center py-2 px-3 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
                  >
                    View Contents
                  </button>
                  <button 
                    onClick={() => {/* TODO: Navigate to add content */}}
                    className="flex-1 text-sm text-center py-2 px-3 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
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
