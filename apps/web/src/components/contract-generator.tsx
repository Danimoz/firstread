"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loading } from "@/components/ui/loading"

interface ContractData {
  contractId?: string
  title?: string
  content: string
  isComplete: boolean
}

export function ContractGenerator() {
  const [prompt, setPrompt] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [contractData, setContractData] = useState<ContractData>({
    content: "",
    isComplete: false
  })
  const [error, setError] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  // Prevent re-applying formatting repeatedly
  const [formattedApplied, setFormattedApplied] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  // Insert a <br/> before sub‑clause numbering like 1.1, 2.3.1 etc when they appear mid-line.
  // We only add a break if the numbering is NOT already at the start of a line (no preceding newline or <br> tag).
  const formatClauseBreaks = (html: string) => {
    if (!html) return html
    return html.replace(/(\d+\.\d+(?:\.\d+)?)(?=\s+[A-Za-z])/g, (match, _p1, offset: number, str: string) => {
      if (offset === 0) return match
      const prevChar = str[offset - 1]
      if (prevChar === '\n') return match
      const lookback = str.slice(Math.max(0, offset - 5), offset).toLowerCase()
      if (lookback.endsWith('<br>') || lookback.endsWith('<br/')) return match
      return '<br/>' + match
    })
  }

  const generateContract = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)
    setError(null)
    setContractData({ content: "", isComplete: false })

    try {
      const response = await fetch("/api/contracts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error("No response body")
      }

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            // Accept empty lines to preserve paragraph breaks
            try {
              if (data.includes('"contract_id"')) {
                const parsed = JSON.parse(data)
                console.log("Contract ID received:", parsed.contract_id)
                setContractData(prev => ({ ...prev, contractId: parsed.contract_id }))
              } else {
                setContractData(prev => ({
                  ...prev,
                  content: prev.content + data + "\n"
                }))
              }
            } catch (e) {
              setContractData(prev => ({
                ...prev,
                content: prev.content + data + "\n"
              }))
            }
          } else if (line.startsWith("event: done")) {
            console.log("Done event received, marking as complete")
            setContractData(prev => ({ ...prev, isComplete: true }))
            break
          } else if (line.startsWith("event: cancelled")) {
            console.log("Cancelled event received")
            setError("Contract generation was cancelled")
            break
          }
        }
      }

      // If we reach here without a done event, mark as complete
      setContractData(prev => {
        if (!prev.isComplete && prev.content) {
          console.log("No done event received, marking as complete based on stream end")
          return { ...prev, isComplete: true }
        }
        return prev
      })
    } catch (err) {
      console.error("Contract generation error:", err)
      setError(err instanceof Error ? err.message : "Failed to generate contract")
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadHTML = () => {
    if (!contractData.content) return

    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Contract</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
        h1 { color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        h2 { color: #374151; margin-top: 30px; margin-bottom: 15px; }
        p { margin-bottom: 15px; text-align: justify; }
        .contract-body { max-width: 800px; margin: 0 auto; }
        .contract-info { background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="contract-info">
        <strong>Contract ID:</strong> ${contractData.contractId || 'N/A'}<br>
        <strong>Generated on:</strong> ${new Date().toLocaleString()}
    </div>
    ${contractData.content}
</body>
</html>`

    const blob = new Blob([htmlContent], { type: "text/html" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `contract-${contractData.contractId || Date.now()}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const stopGeneration = () => {
    if (contractData.contractId) {
      fetch(`/api/contracts/${contractData.contractId}/stop`, { method: "DELETE" })
        .catch(console.error)
    }
    setIsGenerating(false)
  }

  // Auto-show preview when generation is complete
  useEffect(() => {
    if (contractData.isComplete && contractData.content) {
      setShowPreview(true)
    }
  }, [contractData.isComplete, contractData.content])

  // Apply sub-clause formatting once after completion
  useEffect(() => {
    if (contractData.isComplete && !formattedApplied && contractData.content) {
      const formatted = formatClauseBreaks(contractData.content)
      if (formatted !== contractData.content) {
        setContractData(prev => ({ ...prev, content: formatted }))
      }
      setFormattedApplied(true)
    }
  }, [contractData.isComplete, contractData.content, formattedApplied])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Left Panel - Input and Controls */}
      <div className="w-96 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Prompt Input */}
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
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Create a software development contract between a client and developer for a web application project..."
                  className="w-full h-32 p-3 text-base border border-gray-200 dark:border-gray-600 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
                  disabled={isGenerating}
                />
              </div>

              <div className="flex flex-col gap-3">
                <Button
                  onClick={generateContract}
                  disabled={!prompt.trim() || isGenerating}
                  className="w-full h-11 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none"
                >
                  {isGenerating ? (
                    <div className="flex items-center gap-2">
                      <Loading size="sm" className="text-white" />
                      Generating...
                    </div>
                  ) : (
                    "Generate Contract"
                  )}
                </Button>

                {isGenerating && (
                  <Button
                    onClick={stopGeneration}
                    variant="outline"
                    className="w-full h-11 border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
                  >
                    Stop Generation
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Download Controls */}
          {contractData.isComplete && contractData.content && (
            <Card className="shadow-lg border-0 bg-green-50/80 dark:bg-green-900/20 backdrop-blur-sm border-green-200 dark:border-green-800">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-green-900 dark:text-green-200">
                  Contract Ready
                </CardTitle>
                <CardDescription className="text-green-700 dark:text-green-400">
                  Your contract has been generated successfully
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  onClick={downloadHTML}
                  className="w-full h-11 bg-green-600 hover:bg-green-700 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  Download HTML
                </Button>
                <Button
                  onClick={() => setShowPreview(!showPreview)}
                  variant="outline"
                  className="w-full h-11 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800 dark:hover:bg-blue-900/40"
                >
                  {showPreview ? "Hide Preview" : "Show Preview"}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Debug Info */}
          {process.env.NODE_ENV === 'development' && (
            <Card className="border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/20">
              <CardContent className="pt-6">
                <div className="text-gray-700 dark:text-gray-400 text-sm space-y-1">
                  <div>Content Length: {contractData.content.length}</div>
                  <div>Is Complete: {contractData.isComplete.toString()}</div>
                  <div>Contract ID: {contractData.contractId || 'None'}</div>
                  <div>Is Generating: {isGenerating.toString()}</div>
                </div>
              </CardContent>
            </Card>
          )}

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
      </div>

      {/* Right Panel - Canvas */}
      <div className="flex-1 bg-gray-50 dark:bg-gray-800 flex flex-col">
        {contractData.content ? (
          <>
            {/* Canvas Header */}
            <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Generated Contract
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {contractData.isComplete ? "Generation complete" : "Generating..."}
                    {contractData.contractId && ` • ID: ${contractData.contractId}`}
                  </p>
                </div>
                {!contractData.isComplete && (
                  <div className="flex items-center gap-2">
                    <Loading size="sm" className="text-blue-600" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">Generating...</span>
                  </div>
                )}
              </div>
            </div>

            {/* Canvas Content */}
            <div className="flex-1 overflow-y-auto p-8">
              <div className="max-w-4xl mx-auto">
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 min-h-full">
                  <div className="p-8">
                    <div
                      className="prose prose-gray dark:prose-invert max-w-none prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300"
                      dangerouslySetInnerHTML={{ __html: contractData.content }}
                    />

                    {!contractData.isComplete && (
                      <div className="flex items-center justify-center py-8 border-t border-gray-200 dark:border-gray-700 mt-8">
                        <Loading size="md" className="text-blue-600" />
                        <span className="ml-3 text-gray-600 dark:text-gray-400">Generating contract content...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Preview Modal/Panel */}
            {showPreview && contractData.isComplete && (
              <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">HTML Preview</h3>
                    <Button
                      onClick={() => setShowPreview(false)}
                      variant="outline"
                      size="sm"
                    >
                      Close
                    </Button>
                  </div>
                  <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
                    <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden bg-white text-black">
                      <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 border-b border-gray-200 dark:border-gray-600">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                          <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                          <span className="text-sm text-gray-600 dark:text-gray-400 ml-2">HTML Preview</span>
                        </div>
                      </div>
                      <div className="p-6">
                        <div
                          className="prose prose-sm max-w-none text-black"
                          dangerouslySetInnerHTML={{ __html: contractData.content }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Empty State */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-medium text-gray-900 dark:text-white">Ready to Generate</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  Enter your contract description on the left to get started
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 