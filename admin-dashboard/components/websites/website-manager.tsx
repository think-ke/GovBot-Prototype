"use client"

import { useState } from 'react'
import { CrawlTask } from '@/lib/types'

export function WebsiteManager() {
  const [crawlUrl, setCrawlUrl] = useState('')
  const [crawlDepth, setCrawlDepth] = useState(3)
  const [collectionId, setCollectionId] = useState('')
  const [isCrawling, setIsCrawling] = useState(false)
  const [crawlJobs, setCrawlJobs] = useState<CrawlTask[]>([])

  const handleStartCrawl = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!crawlUrl.trim()) return
    if (!collectionId.trim()) {
      alert('Collection ID is required')
      return
    }

    setIsCrawling(true)
    
    try {
      // Here you would implement the actual crawl logic with the required collection ID
      // For now, just simulate the crawl
      await new Promise(resolve => setTimeout(resolve, 1000))
      console.log('Crawl started for:', crawlUrl, 'Collection ID:', collectionId)
      
      // Add to crawl jobs list
      const newJob: CrawlTask = {
        task_id: Date.now().toString(),
        status: 'running',
        seed_urls: [crawlUrl],
        urls_crawled: 0,
        total_urls_queued: 0,
        start_time: new Date().toISOString(),
        finished: false,
        collection_id: collectionId // Add collection_id to the job
      }
      setCrawlJobs(prev => [newJob, ...prev])
      setCrawlUrl('')
    } catch (error) {
      console.error('Crawl failed:', error)
    } finally {
      setIsCrawling(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Website Management</h1>
        <p className="text-muted-foreground">Crawl websites and manage webpage content</p>
      </div>

      {/* Crawl configuration */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="text-lg font-semibold mb-4">Start New Crawl</h3>
        <form onSubmit={handleStartCrawl} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-2">Website URL</label>
              <input
                type="url"
                value={crawlUrl}
                onChange={(e) => setCrawlUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
                disabled={isCrawling}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Crawl Depth</label>
              <select
                value={crawlDepth}
                onChange={(e) => setCrawlDepth(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isCrawling}
              >
                <option value={1}>1 level</option>
                <option value={2}>2 levels</option>
                <option value={3}>3 levels</option>
                <option value={4}>4 levels</option>
                <option value={5}>5 levels</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Collection ID</label>
            <input
              type="text"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              placeholder="Enter collection ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={isCrawling}
            />
            <p className="text-xs text-red-500 mt-1">* Required for organizing crawled webpages</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              type="submit"
              disabled={isCrawling || !crawlUrl.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCrawling ? 'Starting Crawl...' : 'Start Crawl'}
            </button>
            
            <div className="text-sm text-muted-foreground">
              <div className="space-x-4">
                <label className="inline-flex items-center">
                  <input type="checkbox" className="mr-2" />
                  Follow external links
                </label>
                <label className="inline-flex items-center">
                  <input type="checkbox" className="mr-2" defaultChecked />
                  Breadth-first crawling
                </label>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Crawl jobs */}
      <div className="rounded-lg border bg-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Crawl Jobs</h3>
          {crawlJobs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No crawl jobs yet</p>
              <p className="text-sm text-muted-foreground">Start your first website crawl above</p>
            </div>
          ) : (
            <div className="space-y-4">
              {crawlJobs.map((job: any) => (
                <div key={job.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{job.url}</span>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          job.status === 'completed' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {job.status}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        <span>Depth: {job.depth} • </span>
                        <span>Pages found: {job.pagesFound} • </span>
                        <span>Started: {new Date(job.startTime).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button className="text-sm text-blue-600 hover:text-blue-700">View Details</button>
                      <button className="text-sm text-red-600 hover:text-red-700">Stop</button>
                    </div>
                  </div>
                  
                  {job.status === 'running' && (
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '45%' }}></div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
