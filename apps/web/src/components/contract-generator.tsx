"use client"

import { useState } from "react"
import { generateContractHtml } from "@/lib/utils"
import { useContractGeneration } from "@/hooks/use-contract-generation"
import { ContractInput } from "@/components/contract-input"
import { ContractCanvas } from "@/components/contract-canvas"
import { PreviewModal } from "@/components/preview-modal"
import { DownloadControls, DebugInfo } from "@/components/download-controls"

export function ContractGenerator() {
  const [showPreview, setShowPreview] = useState(false)
  const {
    prompt,
    setPrompt,
    isGenerating,
    contractData,
    error,
    hasStartedGenerating,
    generateContract,
    stopGeneration
  } = useContractGeneration()

  const downloadHTML = () => {
    if (!contractData.content) return

    const htmlContent = generateContractHtml({
      contractId: contractData.contractId,
      content: contractData.content
    })

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

  return (
    <>
      {/* ChatGPT-style layout when user hasn't started generating */}
      {!hasStartedGenerating ? (
        <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="max-w-3xl mx-auto">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white text-center">
                Contract Generator
              </h1>
              <p className="text-gray-600 dark:text-gray-400 text-center mt-2">
                Describe the contract you want to generate
              </p>
            </div>
          </div>

          {/* Main content area */}
          <div className="flex-1 flex flex-col justify-center items-center px-4">
            <ContractInput
              prompt={prompt}
              onPromptChange={setPrompt}
              onGenerate={generateContract}
              onStop={stopGeneration}
              isGenerating={isGenerating}
              error={error}
              isInitialView={true}
            />
          </div>
        </div>
      ) : (
        /* Split layout when generating/generated */
        <div className="h-screen flex overflow-hidden">
          {/* Left Panel - Input and Controls */}
          <div className="w-96 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <ContractInput
                prompt={prompt}
                onPromptChange={setPrompt}
                onGenerate={generateContract}
                onStop={stopGeneration}
                isGenerating={isGenerating}
                error={error}
                isInitialView={false}
              />

              <DownloadControls
                isComplete={contractData.isComplete}
                hasContent={!!contractData.content}
                onDownload={downloadHTML}
                onTogglePreview={() => setShowPreview(!showPreview)}
                showPreview={showPreview}
                contractId={contractData.contractId}
                isGenerating={isGenerating}
              />

              <DebugInfo
                contentLength={contractData.content.length}
                isComplete={contractData.isComplete}
                contractId={contractData.contractId}
                isGenerating={isGenerating}
              />
            </div>
          </div>

          {/* Right Panel - Canvas */}
          <div className="flex-1 bg-gray-50 dark:bg-gray-800 flex flex-col">
            <ContractCanvas
              content={contractData.content}
              isComplete={contractData.isComplete}
              contractId={contractData.contractId}
            />
          </div>
        </div>
      )}

      {/* Preview Modal */}
      <PreviewModal
        isOpen={showPreview && !!contractData.content}
        onClose={() => setShowPreview(false)}
        content={contractData.content}
      />
    </>
  )
}