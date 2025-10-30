'use client'

import { useState, useEffect } from 'react'
import { Search, Image as ImageIcon, FileText, Info, AlertCircle } from 'lucide-react'
import ImageUploader from '@/components/ImageUploader'
import DescriptorControls, { DescriptorSettings } from '@/components/DescriptorControls'
import ResultsGrid from '@/components/ResultsGrid'
import { searchByText, searchByImage, searchHybrid, searchByMultiDescriptor, getStats } from '@/lib/api'
import type { FlickrImage, SearchResponse, StatsResponse } from '@/lib/types'

type SearchMode = 'text' | 'image' | 'hybrid'

export default function Home() {
  const [queryText, setQueryText] = useState('')
  const [queryImage, setQueryImage] = useState<string | null>(null)
  const [searchMode, setSearchMode] = useState<SearchMode>('text')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Descriptor settings for multi-descriptor search
  const [descriptorSettings, setDescriptorSettings] = useState<DescriptorSettings>({
    vgg: { enabled: true },
    color: { enabled: true },
    lbp: { enabled: true },
    hog: { enabled: true },
    edge_histogram: { enabled: true },
    sift: { enabled: true }
  })
  
  // Real-time preview settings - removed, no longer needed
  
  // Load stats on mount
  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await getStats()
        setStats(data)
      } catch (err) {
        console.error('Failed to load stats:', err)
      }
    }
    loadStats()
  }, [])

  const handleSearch = async () => {
    if (!queryText && !queryImage) {
      setError('Please provide either an image or text query')
      return
    }

    setLoading(true)
    setError(null)

    try {
      let response: SearchResponse

      if (searchMode === 'hybrid' && queryText && queryImage) {
        response = await searchHybrid({
          query: queryText,
          image_data: queryImage,
          top_k: 50,
        })
      } else if (queryImage) {
        // Use multi-descriptor search
        // Backend automatically prioritizes VGG (50% weight) when present with other descriptors
        response = await searchByMultiDescriptor({
          image_data: queryImage,
          top_k: 50,
          vgg_weight: descriptorSettings.vgg.enabled ? 1.0 : 0,
          color_weight: descriptorSettings.color.enabled ? 1.0 : 0,
          lbp_weight: descriptorSettings.lbp.enabled ? 1.0 : 0,
          hog_weight: descriptorSettings.hog.enabled ? 1.0 : 0,
          edge_histogram_weight: descriptorSettings.edge_histogram.enabled ? 1.0 : 0,
          sift_weight: descriptorSettings.sift.enabled ? 1.0 : 0
        })
        setSearchMode('image')
      } else {
        response = await searchByText({
          query: queryText,
          top_k: 50,
        })
        setSearchMode('text')
      }

      setResults(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleImageSelect = (imageData: string) => {
    setQueryImage(imageData)
    if (queryText) {
      setSearchMode('hybrid')
    } else {
      setSearchMode('image')
    }
  }

  const handleResultImageClick = (image: FlickrImage) => {
    // Use result image as new query
    setQueryImage(image.url)
    setQueryText('')
    setSearchMode('image')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ImageIcon className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Flickr CBIR Search
                </h1>
                <p className="mt-1 text-gray-600">
                  VGG-based visual similarity search with Elasticsearch
                </p>
              </div>
            </div>
            {stats && (
              <div className="bg-blue-50 px-4 py-2 rounded-lg">
                <div className="flex items-center gap-2 text-sm">
                  <Info className="w-4 h-4 text-blue-600" />
                  <span className="text-gray-700">
                    <span className="font-semibold text-blue-600">
                      {stats.total_documents?.toLocaleString() || '0'}
                    </span> images indexed
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section - Top Horizontal Layout */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-blue-600" />
            Search Controls
          </h2>

          {/* Search Controls Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-4">
            {/* Image Upload */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <ImageIcon className="w-4 h-4" />
                Visual Search
              </label>
              <ImageUploader onImageSelect={handleImageSelect} />
            </div>

            {/* Text Search */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <FileText className="w-4 h-4" />
                Text Search
              </label>
              <input
                type="text"
                value={queryText}
                onChange={(e) => {
                  setQueryText(e.target.value)
                  if (queryImage && e.target.value) {
                    setSearchMode('hybrid')
                  }
                }}
                placeholder="Search by tags or title..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>

            {/* Search Button & Mode */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                Action
              </label>
              <button
                onClick={handleSearch}
                disabled={loading || (!queryText && !queryImage)}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2 h-12"
              >
                <Search className="w-5 h-5" />
                <span>
                  {loading ? 'Searching...' : 
                   queryImage ? `Search (${Object.values(descriptorSettings).filter((s: any) => s.enabled).length} descriptors)` : 
                   'Search'}
                </span>
              </button>
            </div>
          </div>

          {/* Search Mode Indicator */}
          {(queryText || queryImage) && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600" />
                <span className="text-gray-700">
                  Search Mode: <span className="font-semibold text-blue-600">
                    {searchMode === 'hybrid' ? 'Hybrid (Text + Image)' : 
                     searchMode === 'image' ? `Visual (${Object.values(descriptorSettings).filter((s: any) => s.enabled).length} descriptors active)` : 
                     'Text (Tags & Title)'}
                  </span>
                </span>
              </div>
            </div>
          )}

          {/* Descriptor Controls - Show only when image is selected */}
          {queryImage && (
            <div className="border-t pt-4">
              <DescriptorControls 
                settings={descriptorSettings} 
                onChange={setDescriptorSettings}
              />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}
        </div>

        {/* Results Section - Full Width */}
        {results && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            {/* Results Header */}
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Search Results
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-semibold">{results.total}</span> results
                  in <span className="font-semibold">{results.took}ms</span>
                </p>
              </div>

              {/* Results Count */}
              <div className="text-sm text-gray-600">
                {results.total} results found
              </div>
            </div>

            {/* Results Display */}
            <ResultsGrid
              results={results.results}
              onImageClick={handleResultImageClick}
            />
          </div>
        )}

        {/* Empty State */}
        {!results && !loading && (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <ImageIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Start Your Search
            </h3>
            <p className="text-gray-500 mb-4">
              Upload an image for visual similarity search or enter keywords
            </p>
            <div className="text-sm text-gray-400 space-y-1">
              <p>• Visual search powered by multiple descriptor types</p>
              <p>• Advanced fuzzy text search for tags and titles</p>
              <p>• Hybrid search combining text and visual features</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 text-sm">
            CBIR System v2.0 - Elasticsearch + VGG16 + Flickr Dataset
          </p>
        </div>
      </footer>
    </div>
  )
}
