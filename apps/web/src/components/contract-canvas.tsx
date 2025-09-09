import { Loading } from "@/components/ui/loading"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface ContractCanvasProps {
  content: string
  isComplete: boolean
  contractId?: string
}

export function ContractCanvas({ content, isComplete, contractId }: ContractCanvasProps) {
  if (!content) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-medium text-gray-900 dark:text-white">Generating Contract</h3>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Please wait while we process your request...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Canvas Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Generated Contract
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {isComplete
                ? "Generation complete • Click 'Edit with AI' to make changes using natural language"
                : "Generating..."
              }
              {contractId && ` • ID: ${contractId}`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isComplete && contractId && (
              <Link href={`/contracts/${contractId}/edit`}>
                <Button variant="outline" size="sm">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Edit with AI
                </Button>
              </Link>
            )}
            {!isComplete && (
              <>
                <Loading size="sm" className="text-blue-600" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Generating...</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Canvas Content */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-h-full">
            <div className="p-8">
              <div
                className="prose prose-gray dark:prose-invert max-w-none prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300"
                dangerouslySetInnerHTML={{ __html: content }}
              />

              {!isComplete && (
                <div className="flex items-center justify-center py-8 border-t border-gray-200 dark:border-gray-700 mt-8">
                  <Loading size="md" className="text-blue-600" />
                  <span className="ml-3 text-gray-600 dark:text-gray-400">Generating contract content...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
