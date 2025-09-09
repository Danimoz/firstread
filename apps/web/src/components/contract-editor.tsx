"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { formatClauseBreaks } from "@/hooks/use-contract-generation"

interface ContractEditorProps {
  contractId: string
  initialTitle: string
  initialContent: string
  onSave: (title: string, content: string) => Promise<void>
  onCancel: () => void
  onCreateVersion: (title: string, content: string) => Promise<void>
  isLoading?: boolean
}

export function ContractEditor({
  contractId,
  initialTitle,
  initialContent,
  onSave,
  onCancel,
  onCreateVersion,
  isLoading = false
}: ContractEditorProps) {
  const [title, setTitle] = useState(initialTitle)
  const [content, setContent] = useState(initialContent)
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const titleChanged = title !== initialTitle
    const contentChanged = content !== initialContent
    setHasChanges(titleChanged || contentChanged)
  }, [title, content, initialTitle, initialContent])

  const handleSave = async () => {
    if (!hasChanges) return

    setIsSaving(true)
    try {
      await onSave(title, content)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCreateVersion = async () => {
    if (!hasChanges) return

    setIsSaving(true)
    try {
      await onCreateVersion(title, content)
    } finally {
      setIsSaving(false)
    }
  }

  const handleContentChange = (newContent: string) => {
    setContent(newContent)
  }

  // Preview the formatted content (read-only)
  const formattedPreview = formatClauseBreaks(content)

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Edit Contract
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={handleCreateVersion}
              disabled={!hasChanges || isSaving}
            >
              Save as New Version
            </Button>
            <Button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-2 gap-4 p-4">
          {/* Editor Panel */}
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Edit Contract</CardTitle>
            </CardHeader>
            <CardContent className="h-full flex flex-col gap-4">
              <div className="space-y-2">
                <Label htmlFor="contract-title">Title</Label>
                <Input
                  id="contract-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Contract title"
                  disabled={isSaving}
                />
              </div>

              <div className="flex-1 space-y-2">
                <Label htmlFor="contract-content">Content</Label>
                <Textarea
                  id="contract-content"
                  value={content}
                  onChange={(e) => handleContentChange(e.target.value)}
                  placeholder="Contract content..."
                  className="h-full resize-none font-mono text-sm"
                  disabled={isSaving}
                />
              </div>
            </CardContent>
          </Card>

          {/* Preview Panel */}
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Preview</CardTitle>
            </CardHeader>
            <CardContent className="h-full overflow-y-auto">
              <div className="bg-white p-6 rounded border min-h-full">
                <h1 className="text-2xl font-bold text-center mb-6 text-black">
                  {title || "Contract Title"}
                </h1>
                <div
                  className="prose prose-sm max-w-none text-black [&_*]:text-black"
                  style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.6'
                  }}
                  dangerouslySetInnerHTML={{ __html: formattedPreview }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Status indicator */}
      {hasChanges && (
        <div className="bg-yellow-50 border-t border-yellow-200 px-4 py-2">
          <p className="text-yellow-800 text-sm">
            You have unsaved changes
          </p>
        </div>
      )}
    </div>
  )
}
