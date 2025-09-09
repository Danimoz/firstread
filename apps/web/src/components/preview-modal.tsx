import { Button } from "@/components/ui/button"

interface PreviewModalProps {
  isOpen: boolean
  onClose: () => void
  content: string
}

export function PreviewModal({ isOpen, onClose, content }: PreviewModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">HTML Preview</h3>
          <Button
            onClick={onClose}
            variant="outline"
            size="sm"
          >
            Close
          </Button>
        </div>
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
          <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden bg-white">
            <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 border-b border-gray-200 dark:border-gray-600">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">HTML Preview</span>
              </div>
            </div>
            <div className="p-6 bg-white">
              <div
                className="prose prose-sm max-w-none text-black [&_*]:text-black [&_h1]:text-black [&_h2]:text-black [&_h3]:text-black [&_p]:text-black [&_div]:text-black [&_span]:text-black"
                style={{
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.6'
                }}
                dangerouslySetInnerHTML={{ __html: content }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
