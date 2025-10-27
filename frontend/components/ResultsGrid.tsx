'use client'

import { ImageResult } from '@/lib/types'

interface ResultsGridProps {
  results: ImageResult[]
  onImageClick: (imageUrl: string) => void
}

export default function ResultsGrid({ results, onImageClick }: ResultsGridProps) {
  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No results found</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {results.map((result) => (
        <div
          key={result.id}
          className="group relative bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => onImageClick(result.url)}
        >
          {/* Image */}
          <div className="aspect-square bg-gray-100 relative overflow-hidden">
            <img
              src={`http://localhost:8000${result.url}`}
              alt={result.filename}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
              loading="lazy"
            />
            
            {/* Similarity Score Badge */}
            <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
              {(1 - result.score).toFixed(3)}
            </div>
          </div>

          {/* Image Info */}
          <div className="p-3">
            <p className="text-sm font-medium text-gray-900 truncate">
              {result.filename}
            </p>
            
            {result.tags && (
              <p className="text-xs text-gray-500 mt-1 truncate">
                {result.tags}
              </p>
            )}
            
            {result.caption && (
              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                {result.caption}
              </p>
            )}

            {/* Distance Score */}
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-gray-500">Distance:</span>
              <span className="font-mono text-gray-700">
                {result.score.toFixed(4)}
              </span>
            </div>
          </div>

          {/* Hover Overlay */}
          <div className="absolute inset-0 bg-blue-500 bg-opacity-0 group-hover:bg-opacity-10 transition-all pointer-events-none" />
        </div>
      ))}
    </div>
  )
}
