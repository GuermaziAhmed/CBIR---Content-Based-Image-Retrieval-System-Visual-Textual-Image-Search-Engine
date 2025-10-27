'use client'

import { FlickrImage } from '@/lib/types'
import { MapPin, Eye, Calendar, Tag } from 'lucide-react'

interface ImageCardProps {
  image: FlickrImage
  onClick: (image: FlickrImage) => void
}

export default function ImageCard({ image, onClick }: ImageCardProps) {
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`
    return views.toString()
  }

  return (
    <div
      className="group relative bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer"
      onClick={() => onClick(image)}
    >
      {/* Image */}
      <div className="aspect-square bg-gray-100 relative overflow-hidden">
        <img
          src={image.url}
          alt={image.title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          loading="lazy"
        />
        
        {/* Similarity Score Badge (if available) */}
        {image.score !== undefined && (
          <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white text-xs font-semibold px-2 py-1 rounded">
            {(image.score * 100).toFixed(1)}%
          </div>
        )}

        {/* Location Badge */}
        {image.latitude && image.longitude && (
          <div className="absolute top-2 left-2 bg-blue-600 bg-opacity-90 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            <span>Located</span>
          </div>
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>

      {/* Metadata */}
      <div className="p-3">
        {/* Title */}
        <h3 className="font-semibold text-sm text-gray-900 line-clamp-2 mb-2 min-h-[2.5rem]">
          {image.title || 'Untitled'}
        </h3>

        {/* Tags */}
        {image.tags && (
          <div className="flex items-start gap-1 mb-2">
            <Tag className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-600 line-clamp-2">
              {image.tags.split(',').slice(0, 3).join(', ')}
            </p>
          </div>
        )}

        {/* Stats Row */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          {/* Views */}
          <div className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            <span>{formatViews(image.views)}</span>
          </div>

          {/* Date Taken */}
          {image.date_taken && (
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{formatDate(image.date_taken)}</span>
            </div>
          )}
        </div>

        {/* Location Info */}
        {image.latitude && image.longitude && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <div className="text-xs text-gray-500 flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              <span>
                {image.latitude.toFixed(4)}, {image.longitude.toFixed(4)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
