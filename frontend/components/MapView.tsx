'use client'

import { useEffect, useRef } from 'react'
import { FlickrImage } from '@/lib/types'

interface MapViewProps {
  images: FlickrImage[]
  onImageClick: (image: FlickrImage) => void
}

export default function MapView({ images, onImageClick }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<any>(null)
  const markersRef = useRef<any[]>([])

  useEffect(() => {
    // Dynamically import Leaflet only on client side
    if (typeof window === 'undefined') return

    const initMap = async () => {
      const L = (await import('leaflet')).default
      await import('leaflet/dist/leaflet.css')

      // Fix for default marker icons in webpack
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      if (mapRef.current && !mapInstanceRef.current) {
        // Initialize map
        mapInstanceRef.current = L.map(mapRef.current).setView([20, 0], 2)

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 19,
        }).addTo(mapInstanceRef.current)
      }
    }

    initMap()

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (!mapInstanceRef.current) return

    const updateMarkers = async () => {
      const L = (await import('leaflet')).default

      // Clear existing markers
      markersRef.current.forEach(marker => marker.remove())
      markersRef.current = []

      // Filter images with valid coordinates
      const validImages = images.filter(
        img => img.latitude !== null && img.longitude !== null
      )

      if (validImages.length === 0) return

      // Create custom icon
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div class="w-8 h-8 bg-blue-600 border-2 border-white rounded-full shadow-lg flex items-center justify-center">
          <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
          </svg>
        </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16],
      })

      // Add markers for each image
      validImages.forEach(image => {
        const marker = L.marker([image.latitude!, image.longitude!], {
          icon: customIcon,
        }).addTo(mapInstanceRef.current)

        // Create popup content
        const popupContent = `
          <div class="w-48">
            <img src="${image.url}" alt="${image.title}" class="w-full h-32 object-cover rounded mb-2" />
            <h3 class="font-semibold text-sm mb-1">${image.title || 'Untitled'}</h3>
            <p class="text-xs text-gray-600 mb-1">${image.views.toLocaleString()} views</p>
            ${image.tags ? `<p class="text-xs text-gray-500 truncate">${image.tags}</p>` : ''}
          </div>
        `

        marker.bindPopup(popupContent)
        marker.on('click', () => onImageClick(image))

        markersRef.current.push(marker)
      })

      // Fit bounds to show all markers
      if (validImages.length > 0) {
        const bounds = L.latLngBounds(
          validImages.map(img => [img.latitude!, img.longitude!])
        )
        mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] })
      }
    }

    updateMarkers()
  }, [images, onImageClick])

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full rounded-lg" />
      {images.filter(img => img.latitude !== null && img.longitude !== null).length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <p className="text-gray-500">No images with location data</p>
        </div>
      )}
    </div>
  )
}
