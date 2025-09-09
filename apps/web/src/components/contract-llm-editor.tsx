"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { formatClauseBreaks } from "@/hooks/use-contract-generation"
import { Loading } from "@/components/ui/loading"

interface ContractLLMEditorProps {
  contractId: string
  initialTitle: string
  initialContent: string
  onEditComplete: (newContractId: string) => void
  onCancel: () => void
}

interface EditSuggestion {
  text: string
  isSelected: boolean
}

export function ContractLLMEditor({
  contractId,
  initialTitle,
  initialContent,
  onEditComplete,
  onCancel
}: ContractLLMEditorProps) {
  const [editPrompt, setEditPrompt] = useState("")
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState("")
  const [suggestions, setSuggestions] = useState<EditSuggestion[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load suggestions when component mounts
  useEffect(() => {
    loadSuggestions()
  }, [contractId])

  const loadSuggestions = async () => {
    setLoadingSuggestions(true)
    try {
      const response = await fetch(`/api/contracts/${contractId}/suggestions`)
      if (response.ok) {
        const data = await response.json()
        setSuggestions(data.suggestions.map((text: string) => ({ text, isSelected: false })))
      }
    } catch (err) {
      console.error("Failed to load suggestions:", err)
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleStopEdit = async () => {
    try {
      await fetch(`/api/contracts/${contractId}/stop`, { method: "DELETE" })
      setIsEditing(false)
      setError("Edit stopped by user")
    } catch (err) {
      console.error("Failed to stop edit:", err)
    }
  }

  const handleEditContract = async () => {
    if (!editPrompt.trim()) return

    setIsEditing(true)
    setError(null)
    setEditedContent("")

    try {
      const response = await fetch(`/api/contracts/${contractId}/edit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ edit_prompt: editPrompt.trim() })
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
            try {
              if (data.includes('"new_contract_id"')) {
                const parsed = JSON.parse(data)
                onEditComplete(parsed.new_contract_id)
                return
              } else if (data.includes('"edit_id"')) {
                // Edit started
                continue
              } else {
                // Content chunk
                setEditedContent(prev => prev + data)
              }
            } catch (e) {
              // Regular content chunk
              setEditedContent(prev => prev + data)
            }
          } else if (line.startsWith("event: edit_complete")) {
            break
          } else if (line.startsWith("event: cancelled")) {
            setError("Edit was cancelled")
            break
          } else if (line.startsWith("event: error")) {
            setError("Edit failed")
            break
          }
        }
      }
    } catch (err) {
      console.error("Edit error:", err)
      setError(err instanceof Error ? err.message : "Failed to edit contract")
    } finally {
      setIsEditing(false)
    }
  }

  const handleSuggestionClick = (suggestionText: string) => {
    setEditPrompt(suggestionText)
  }

  const displayContent = editedContent || initialContent
  const formattedContent = formatClauseBreaks(displayContent)

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Edit Contract with AI
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Describe the changes you want to make to the contract
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={isEditing}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-2 gap-4 p-4">
          {/* Edit Panel */}
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Edit Instructions</CardTitle>
            </CardHeader>
            <CardContent className="h-full flex flex-col gap-4">
              {/* Edit Prompt Input */}
              <div className="space-y-2">
                <Label htmlFor="edit-prompt">What changes would you like to make?</Label>
                <Textarea
                  id="edit-prompt"
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  placeholder="e.g., Make the payment terms more flexible, Add a termination clause, Change the delivery date to 30 days..."
                  className="h-32 resize-none"
                  disabled={isEditing}
                />
              </div>

              {/* Edit Button */}
              <div className="flex gap-2">
                <Button
                  onClick={handleEditContract}
                  disabled={!editPrompt.trim() || isEditing}
                  className="flex-1"
                >
                  {isEditing ? (
                    <>
                      <Loading size="sm" className="mr-2" />
                      Editing Contract...
                    </>
                  ) : (
                    "Edit Contract"
                  )}
                </Button>

                {isEditing && (
                  <Button
                    variant="outline"
                    onClick={handleStopEdit}
                    className="px-4"
                  >
                    Stop
                  </Button>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

              {/* Suggestions */}
              <div className="flex-1 space-y-2">
                <Label>Suggested Edits</Label>
                {loadingSuggestions ? (
                  <div className="flex items-center justify-center py-8">
                    <Loading size="sm" className="mr-2" />
                    <span className="text-sm text-gray-600">Loading suggestions...</span>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion.text)}
                        className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 rounded-md text-sm transition-colors"
                        disabled={isEditing}
                      >
                        {suggestion.text}
                      </button>
                    ))}
                    {suggestions.length === 0 && !loadingSuggestions && (
                      <p className="text-sm text-gray-500 text-center py-4">
                        No suggestions available
                      </p>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Preview Panel */}
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  {editedContent ? "Edited Contract" : "Current Contract"}
                </CardTitle>
                {isEditing && (
                  <div className="flex items-center gap-2">
                    <Loading size="sm" className="text-blue-600" />
                    <span className="text-sm text-gray-600">Generating edits...</span>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="h-full overflow-y-auto">
              <div className="bg-white p-6 rounded border min-h-full">
                <h1 className="text-2xl font-bold text-center mb-6 text-black">
                  {initialTitle}
                </h1>
                <div
                  className="prose prose-sm max-w-none text-black [&_*]:text-black"
                  style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.6'
                  }}
                  dangerouslySetInnerHTML={{ __html: formattedContent }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Status indicator */}
      {isEditing && (
        <div className="bg-blue-50 border-t border-blue-200 px-4 py-2">
          <p className="text-blue-800 text-sm">
            AI is editing your contract...
          </p>
        </div>
      )}
    </div>
  )
}
