"use client"

import { useState } from 'react'
import { Collection } from '@/lib/types'

export function CollectionManager() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [newCollectionName, setNewCollectionName] = useState('')
  const [newCollectionDescription, setNewCollectionDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)

  const handleCreateCollection = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!newCollectionName.trim()) return

    setIsCreating(true)
    
    try {
      // Here you would implement the actual collection creation logic
      // For now, just simulate the creation
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const newCollection: Collection = {
        id: Date.now().toString(),
        name: newCollectionName,
        description: newCollectionDescription,
        type: 'mixed' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by: 'admin', // TODO: Replace with actual user ID
        document_count: 0,
        webpage_count: 0,
        total_size: 0
      }
      
      setCollections(prev => [newCollection, ...prev])
      setNewCollectionName('')
      setNewCollectionDescription('')
      setShowCreateForm(false)
    } catch (error) {
      console.error('Collection creation failed:', error)
    } finally {
      setIsCreating(false)
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
        {collections.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📁</span>
            </div>
            <p className="text-muted-foreground mb-2">No collections yet</p>
            <p className="text-sm text-muted-foreground">Create your first collection to organize your content</p>
          </div>
        ) : (
          collections.map((collection: any) => (
            <div key={collection.id} className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">{collection.name}</h3>
                  {collection.description && (
                    <p className="text-sm text-muted-foreground mb-2">{collection.description}</p>
                  )}
                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    <span>{collection.document_count} documents</span>
                    <span>{collection.webpage_count} webpages</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="text-sm text-blue-600 hover:text-blue-700">Edit</button>
                  <button className="text-sm text-red-600 hover:text-red-700">Delete</button>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Storage Used</span>
                  <span className="font-medium">{collection.total_size || 0} KB</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Created</span>
                  <span className="font-medium">{new Date(collection.created_at).toLocaleDateString()}</span>
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
