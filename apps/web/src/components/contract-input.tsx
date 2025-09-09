import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loading } from "@/components/ui/loading"

interface ContractInputProps {
  prompt: string
  onPromptChange: (prompt: string) => void
  onGenerate: () => void
  onStop: () => void
  isGenerating: boolean
  error: string | null
  isInitialView: boolean
}

export function ContractInput({
  prompt,
  onPromptChange,
  onGenerate,
  onStop,
  isGenerating,
  error,
  isInitialView
}: ContractInputProps) {
  if (isInitialView) {
    return (
      <div className="w-full max-w-3xl space-y-6">
        {/* Welcome message */}
        <div className="text-center space-y-4 mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            What contract would you like to create?
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Be specific about the type, parties involved, and key terms. I&apos;ll generate a comprehensive legal document for you.
          </p>
        </div>

        {/* Input area */}
        <Card className="shadow-xl border-0 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => onPromptChange(e.target.value)}
                placeholder="e.g., Create a software development contract between a client and developer for a web application project with milestone-based payments, intellectual property clauses, and a 6-month timeline..."
                className="w-full h-32 p-4 text-base border border-gray-200 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                disabled={isGenerating}
              />

              <div className="flex justify-end">
                <Button
                  onClick={onGenerate}
                  disabled={!prompt.trim() || isGenerating}
                  className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGenerating ? (
                    <div className="flex items-center gap-2">
                      <Loading size="sm" className="text-white" />
                      Starting...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                      Generate Contract
                    </div>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <CardContent className="pt-6">
              <div className="text-red-700 dark:text-red-400 text-center">
                {error}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  // Side panel view
  return (
    <Card className="shadow-lg border-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="text-xl font-bold text-gray-900 dark:text-white">
          Generate Contract
        </CardTitle>
        <CardDescription className="text-gray-600 dark:text-gray-400">
          Describe the contract you want to generate. Be specific about the type, parties involved, and key terms.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="prompt" className="text-gray-700 dark:text-gray-300">
            Contract Description
          </Label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            placeholder="e.g., Create a software development contract between a client and developer for a web application project..."
            className="w-full h-32 p-3 text-base border border-gray-200 dark:border-gray-600 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            disabled={isGenerating}
          />
        </div>

        <div className="flex flex-col gap-3">
          <Button
            onClick={onGenerate}
            disabled={!prompt.trim() || isGenerating}
            className="w-full h-11 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none"
          >
            {isGenerating ? (
              <div className="flex items-center gap-2">
                <Loading size="sm" className="text-white" />
                Generating...
              </div>
            ) : (
              "Generate New Contract"
            )}
          </Button>

          {isGenerating && (
            <Button
              onClick={onStop}
              variant="outline"
              className="w-full h-11 border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
            >
              Stop Generation
            </Button>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 rounded-md text-sm bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">
            {error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
