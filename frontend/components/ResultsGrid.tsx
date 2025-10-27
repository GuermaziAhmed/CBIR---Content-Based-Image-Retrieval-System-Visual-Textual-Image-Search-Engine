'use client'

import { FlickrImage } from '@/lib/types'
import ImageCard from './ImageCard'

interface ResultsGridProps {
  results: FlickrImage[]
  onImageClick: (image: FlickrImage) => void
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
      {results.map((image) => (
        <ImageCard
          key={image.id}
          image={image}
          onClick={onImageClick}
        />
      ))}
    </div>
  )
}
