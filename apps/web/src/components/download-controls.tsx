import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface DownloadControlsProps {
  isComplete: boolean
  hasContent: boolean
  onDownload: () => void
  onTogglePreview: () => void
  showPreview: boolean
  contractId?: string
  isGenerating: boolean
}

export function DownloadControls({
  isComplete,
  hasContent,
  onDownload,
  onTogglePreview,
  showPreview,
  contractId,
  isGenerating
}: DownloadControlsProps) {
  if (!hasContent) return null

  return (
    <Card className="shadow-lg border-0 bg-green-50/80 dark:bg-green-900/20 backdrop-blur-sm border-green-200 dark:border-green-800">
      <CardHeader>
        <CardTitle className="text-lg font-bold text-green-900 dark:text-green-200">
          {isComplete ? "Contract Ready" : isGenerating ? "Contract In Progress" : "Contract Available"}
        </CardTitle>
        <CardDescription className="text-green-700 dark:text-green-400">
          {isComplete
            ? "Your contract has been generated successfully"
            : isGenerating
              ? "You can download the current progress"
              : "Generation was stopped - you can still download what was generated"
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button
          onClick={onDownload}
          className="w-full h-11 bg-green-600 hover:bg-green-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Download HTML
        </Button>
        <Button
          onClick={onTogglePreview}
          variant="outline"
          className="w-full h-11 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800 dark:hover:bg-blue-900/40"
        >
          {showPreview ? "Hide Preview" : "Show Preview"}
        </Button>
      </CardContent>
    </Card>
  )
}

interface DebugInfoProps {
  contentLength: number
  isComplete: boolean
  contractId?: string
  isGenerating: boolean
}

export function DebugInfo({ contentLength, isComplete, contractId, isGenerating }: DebugInfoProps) {
  if (process.env.NODE_ENV !== 'development') return null

  return (
    <Card className="border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/20">
      <CardContent className="pt-6">
        <div className="text-gray-700 dark:text-gray-400 text-sm space-y-1">
          <div>Content Length: {contentLength}</div>
          <div>Is Complete: {isComplete.toString()}</div>
          <div>Contract ID: {contractId || 'None'}</div>
          <div>Is Generating: {isGenerating.toString()}</div>
        </div>
      </CardContent>
    </Card>
  )
}
