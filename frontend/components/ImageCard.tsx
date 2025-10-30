'use client'

import { FlickrImage } from '@/lib/types'
import { MapPin, Eye, Calendar, Tag, Brain, Palette, Grid, Zap, Aperture, Key } from 'lucide-react'

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

  // Descriptor info with icons and colors
  const descriptorInfo = {
    vgg: { label: 'VGG', icon: Brain, color: 'bg-purple-500' },
    color: { label: 'Color', icon: Palette, color: 'bg-pink-500' },
    lbp: { label: 'LBP', icon: Grid, color: 'bg-blue-500' },
    hog: { label: 'HOG', icon: Zap, color: 'bg-yellow-500' },
    edge_histogram: { label: 'Edge', icon: Aperture, color: 'bg-green-500' },
    sift: { label: 'SIFT', icon: Key, color: 'bg-indigo-500' },
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
        
        {/* Global Match Badge (if available) */}
        {image.global_match !== undefined && (
          <div className="absolute top-2 right-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-lg">
            {image.global_match.toFixed(1)}%
          </div>
        )}

        {/* Simple Score Badge (fallback) */}
        {image.score !== undefined && image.global_match === undefined && (
          <div className="absolute top-2 right-2 bg-black bg-opacity-70 text-white text-xs font-semibold px-2 py-1 rounded">
            {(image.score * 100).toFixed(1)}%
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

        {/* Descriptor Scores (if available) */}
        {image.descriptor_scores && Object.keys(image.descriptor_scores).length > 0 && (
          <div className="mb-3 space-y-1.5">
            {Object.entries(image.descriptor_scores).map(([key, value]) => {
              const info = descriptorInfo[key as keyof typeof descriptorInfo]
              if (!info || value === undefined) return null
              
              const Icon = info.icon
              return (
                <div key={key} className="flex items-center gap-2">
                  <div className="flex items-center gap-1 w-20 text-xs font-medium text-gray-600">
                    <Icon className="w-3 h-3" />
                    <span>{info.label}</span>
                  </div>
                  <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${info.color} transition-all duration-500`}
                      style={{ width: `${Math.min(100, value)}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-gray-700 w-10 text-right">
                    {value.toFixed(0)}%
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {/* Tags */}
        {image.tags && (
          <div className="mb-2">
            <div className="flex items-center gap-1 mb-1">
              <Tag className="w-3 h-3 text-gray-400" />
              <span className="text-xs font-medium text-gray-500">Tags:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {image.tags.split(',').slice(0, 5).map((tag, index) => (
                <span
                  key={index}
                  className="inline-block bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full border border-blue-200"
                >
                  {tag.trim()}
                </span>
              ))}
              {image.tags.split(',').length > 5 && (
                <span className="inline-block text-xs text-gray-400 px-1 py-0.5">
                  +{image.tags.split(',').length - 5} more
                </span>
              )}
            </div>
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
      </div>
    </div>
  )
}
