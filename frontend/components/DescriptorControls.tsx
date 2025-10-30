'use client'

import { Brain, Palette, Grid, Zap, CheckSquare, Aperture, Key } from 'lucide-react'
import { useState } from 'react'

export interface DescriptorSettings {
  vgg: { enabled: boolean }
  color: { enabled: boolean }
  lbp: { enabled: boolean }
  hog: { enabled: boolean }
  edge_histogram: { enabled: boolean }
  sift: { enabled: boolean }
}

interface DescriptorControlsProps {
  settings: DescriptorSettings
  onChange: (settings: DescriptorSettings) => void
}

const descriptorInfo = {
  vgg: {
    label: 'VGG Deep Learning',
    icon: Brain,
    color: 'purple',
    description: 'Deep neural network features - best for overall similarity'
  },
  color: {
    label: 'Color Histogram',
    icon: Palette,
    color: 'red',
    description: 'RGB color distribution - finds images with similar colors'
  },
  lbp: {
    label: 'LBP Texture',
    icon: Grid,
    color: 'blue',
    description: 'Local Binary Pattern - captures texture patterns'
  },
  hog: {
    label: 'HOG Edges',
    icon: Zap,
    color: 'yellow',
    description: 'Histogram of Gradients - captures shapes and edges'
  },
  edge_histogram: {
    label: 'Edge Histogram',
    icon: Aperture,
    color: 'green',
    description: 'Edge orientation distribution - directional edge patterns'
  },
  sift: {
    label: 'SIFT Features',
    icon: Key,
    color: 'indigo',
    description: 'Scale-Invariant Feature Transform - local keypoint descriptors'
  }
}

export default function DescriptorControls({ settings, onChange }: DescriptorControlsProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const handleToggle = (descriptor: keyof DescriptorSettings) => {
    onChange({
      ...settings,
      [descriptor]: {
        enabled: !settings[descriptor].enabled
      }
    })
  }

  const handleSelectAll = () => {
    onChange({
      vgg: { enabled: true },
      color: { enabled: true },
      lbp: { enabled: true },
      hog: { enabled: true },
      edge_histogram: { enabled: true },
      sift: { enabled: true }
    })
  }

  const handleDeselectAll = () => {
    onChange({
      vgg: { enabled: false },
      color: { enabled: false },
      lbp: { enabled: false },
      hog: { enabled: false },
      edge_histogram: { enabled: false },
      sift: { enabled: false }
    })
  }

  const enabledCount = Object.values(settings).filter(s => s.enabled).length

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <CheckSquare className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-gray-900">
            Select Descriptors
          </span>
          <span className="text-sm text-gray-500">
            ({enabledCount} selected)
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Quick Actions */}
          <div className="flex gap-2">
            <button
              onClick={handleSelectAll}
              className="flex-1 px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded transition-colors"
            >
              Select All
            </button>
            <button
              onClick={handleDeselectAll}
              className="flex-1 px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 text-gray-700 rounded transition-colors"
            >
              Clear All
            </button>
          </div>

          {/* Descriptor Checkboxes */}
          <div className="space-y-2">
            {(Object.keys(descriptorInfo) as Array<keyof DescriptorSettings>).map((key) => {
              const info = descriptorInfo[key]
              const Icon = info.icon
              const isEnabled = settings[key].enabled

              return (
                <label
                  key={key}
                  className={`flex items-start gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    isEnabled
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={() => handleToggle(key)}
                    className="mt-1 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-5 h-5 text-${info.color}-600`} />
                      <span className="font-medium text-gray-900">{info.label}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{info.description}</p>
                  </div>
                </label>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
