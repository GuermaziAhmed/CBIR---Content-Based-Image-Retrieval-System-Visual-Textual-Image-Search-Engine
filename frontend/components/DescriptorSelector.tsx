'use client'

interface DescriptorSelectorProps {
  selected: string[]
  onChange: (selected: string[]) => void
}

const descriptors = [
  {
    id: 'color',
    name: 'Color Histogram',
    description: 'RGB color distribution',
  },
  {
    id: 'lbp',
    name: 'LBP',
    description: 'Local Binary Patterns (texture)',
  },
  {
    id: 'hog',
    name: 'HOG',
    description: 'Histogram of Oriented Gradients (edges)',
  },
  {
    id: 'mpeg7',
    name: 'MPEG-7',
    description: 'Standard visual descriptors',
  },
]

export default function DescriptorSelector({ selected, onChange }: DescriptorSelectorProps) {
  const toggleDescriptor = (id: string) => {
    if (selected.includes(id)) {
      // Don't allow deselecting if it's the last one
      if (selected.length === 1) {
        return
      }
      onChange(selected.filter((d) => d !== id))
    } else {
      onChange([...selected, id])
    }
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {descriptors.map((descriptor) => {
        const isSelected = selected.includes(descriptor.id)
        return (
          <button
            key={descriptor.id}
            onClick={() => toggleDescriptor(descriptor.id)}
            className={`p-4 rounded-lg border-2 text-left transition-all ${
              isSelected
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  {descriptor.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {descriptor.description}
                </p>
              </div>
              <div
                className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                  isSelected
                    ? 'bg-blue-500 border-blue-500'
                    : 'border-gray-300'
                }`}
              >
                {isSelected && (
                  <svg
                    className="w-3 h-3 text-white"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path d="M5 13l4 4L19 7"></path>
                  </svg>
                )}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
