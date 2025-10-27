'use client'

import { useState } from 'react'
import { Search, Image as ImageIcon, FileText } from 'lucide-react'
import ImageUploader from '@/components/ImageUploader'
import DescriptorSelector from '@/components/DescriptorSelector'
import ResultsGrid from '@/components/ResultsGrid'
import { searchImages } from '@/lib/api'
import type { SearchRequest, SearchResponse } from '@/lib/types'

export default function Home() {
  const [queryText, setQueryText] = useState('')
  const [queryImage, setQueryImage] = useState<string | null>(null)
  const [selectedDescriptors, setSelectedDescriptors] = useState(['color', 'lbp'])
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!queryText && !queryImage) {
      setError('Please provide either an image or text query')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request: SearchRequest = {
        query_text: queryText || undefined,
        image_data: queryImage || undefined,
        use_image: !!queryImage,
        descriptors: selectedDescriptors,
        top_k: 50,
        combine_mode: 'fusion'
      }

      const response = await searchImages(request)
      setResults(response)
    } catch (err: any) {
      setError(err.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleImageSelect = (imageData: string) => {
    setQueryImage(imageData)
  }

  const handleResultImageClick = (imageUrl: string) => {
    // Use result image as new query
    setQueryImage(imageUrl)
    setQueryText('')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <ImageIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              CBIR Image Search
            </h1>
          </div>
          <p className="mt-2 text-gray-600">
            Search by image or text using advanced visual descriptors
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Image Upload */}
            <div>
              <h2 className="text-lg font-semibold mb-3 flex items-center">
                <ImageIcon className="w-5 h-5 mr-2" />
                Visual Search
              </h2>
              <ImageUploader onImageSelect={handleImageSelect} />
            </div>

            {/* Text Search */}
            <div>
              <h2 className="text-lg font-semibold mb-3 flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Text Search
              </h2>
              <input
                type="text"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Enter keywords (e.g., cat, red car)..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <p className="mt-2 text-sm text-gray-500">
                Search by tags, captions, or filenames
              </p>
            </div>
          </div>

          {/* Descriptor Selection */}
          <div className="mt-6">
            <h2 className="text-lg font-semibold mb-3">
              Select Descriptors
            </h2>
            <DescriptorSelector
              selected={selectedDescriptors}
              onChange={setSelectedDescriptors}
            />
          </div>

          {/* Search Button */}
          <div className="mt-6">
            <button
              onClick={handleSearch}
              disabled={loading || (!queryText && !queryImage)}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Search className="w-5 h-5" />
              <span>{loading ? 'Searching...' : 'Search Images'}</span>
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        {results && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">
                Search Results
              </h2>
              <div className="text-sm text-gray-600">
                <span className="font-semibold">{results.total_results}</span> results
                in <span className="font-semibold">{results.search_time_ms}ms</span>
              </div>
            </div>

            <div className="mb-4 text-sm text-gray-600">
              Descriptors used: {results.descriptors_used.join(', ')}
            </div>

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
            <p className="text-gray-500">
              Upload an image or enter keywords to find similar images
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 text-sm">
            CBIR System v1.0 - Content-Based Image Retrieval using MPEG-7 Descriptors
          </p>
        </div>
      </footer>
    </div>
  )
}
