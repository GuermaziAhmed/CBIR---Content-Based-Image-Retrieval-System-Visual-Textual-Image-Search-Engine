'use client'

import { useState, useEffect, Suspense, lazy } from 'react'
import { Search, Image as ImageIcon, FileText, Map, Grid, Info } from 'lucide-react'
import ImageUploader from '@/components/ImageUploader'
import FilterPanel, { Filters } from '@/components/FilterPanel'
import ResultsGrid from '@/components/ResultsGrid'
import { searchByText, searchByImage, searchHybrid, getStats } from '@/lib/api'
import type { FlickrImage, SearchResponse, StatsResponse } from '@/lib/types'

// Lazy load MapView to avoid SSR issues with Leaflet
const MapView = lazy(() => import('@/components/MapView'))

type ViewMode = 'grid' | 'map'
type SearchMode = 'text' | 'image' | 'hybrid'

export default function Home() {
  const [queryText, setQueryText] = useState('')
  const [queryImage, setQueryImage] = useState<string | null>(null)
  const [searchMode, setSearchMode] = useState<SearchMode>('text')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filters, setFilters] = useState<Filters>({
    tags: [],
    dateFrom: undefined,
    dateTo: undefined,
    minViews: undefined,
  })
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        response = await searchByImage({
          image_data: queryImage,
          top_k: 50,
          tags: filters.tags.length > 0 ? filters.tags : undefined,
          date_from: filters.dateFrom,
          date_to: filters.dateTo,
        })
        setSearchMode('image')
      } else {
        response = await searchByText({
          query: queryText,
          top_k: 50,
          tags: filters.tags.length > 0 ? filters.tags : undefined,
          date_from: filters.dateFrom,
          date_to: filters.dateTo,
          min_views: filters.minViews,
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
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Search & Filters */}
          <div className="lg:col-span-1 space-y-6">
            {/* Search Section */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Search</h2>

              {/* Image Upload */}
              <div className="mb-4">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                  <ImageIcon className="w-4 h-4" />
                  Visual Search
                </label>
                <ImageUploader onImageSelect={handleImageSelect} />
              </div>

              {/* Text Search */}
              <div className="mb-4">
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
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>

              {/* Search Mode Indicator */}
              {(queryText || queryImage) && (
                <div className="mb-4 p-2 bg-gray-50 rounded text-xs text-gray-600">
                  Mode: <span className="font-semibold text-blue-600">
                    {searchMode === 'hybrid' ? 'Hybrid (Text + Image)' : 
                     searchMode === 'image' ? 'Visual (VGG Features)' : 
                     'Text (Tags & Title)'}
                  </span>
                </div>
              )}

              {/* Search Button */}
              <button
                onClick={handleSearch}
                disabled={loading || (!queryText && !queryImage)}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded transition-colors flex items-center justify-center space-x-2"
              >
                <Search className="w-5 h-5" />
                <span>{loading ? 'Searching...' : 'Search'}</span>
              </button>

              {/* Error Display */}
              {error && (
                <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded">
                  {error}
                </div>
              )}
            </div>

            {/* Filters */}
            <FilterPanel filters={filters} onChange={setFilters} />
          </div>

          {/* Right Content - Results */}
          <div className="lg:col-span-3">
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

                  {/* View Mode Toggle */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`p-2 rounded ${
                        viewMode === 'grid'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                      title="Grid View"
                    >
                      <Grid className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setViewMode('map')}
                      className={`p-2 rounded ${
                        viewMode === 'map'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                      title="Map View"
                    >
                      <Map className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Results Display */}
                {viewMode === 'grid' ? (
                  <ResultsGrid
                    results={results.results}
                    onImageClick={handleResultImageClick}
                  />
                ) : (
                  <div className="h-[600px]">
                    <Suspense fallback={<div className="flex items-center justify-center h-full">Loading map...</div>}>
                      <MapView
                        images={results.results}
                        onImageClick={handleResultImageClick}
                      />
                    </Suspense>
                  </div>
                )}
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
                  <p>• Visual search powered by VGG16 deep features</p>
                  <p>• Search by tags, title, location, and dates</p>
                  <p>• View results on interactive map</p>
                </div>
              </div>
            )}
          </div>
        </div>
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
