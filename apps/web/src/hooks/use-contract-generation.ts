import { useState, useRef, useEffect, useMemo } from "react"

interface ContractData {
  contractId?: string
  title?: string
  content: string
  isComplete: boolean
}

// Export the formatting function for use in other components
export function formatClauseBreaks(html: string) {
  if (!html) return html

  // First, handle numbered sub-sections (e.g., 1.1, 2.3, 5.5.1)
  let formatted = html.replace(/(\d+\.\d+(?:\.\d+)?)(?=\s+[A-Za-z])/g, (match, _p1, offset: number, str: string) => {
    if (offset === 0) return match
    const prevChar = str[offset - 1]
    if (prevChar === '\n') return match
    const lookback = str.slice(Math.max(0, offset - 5), offset).toLowerCase()
    if (lookback.endsWith('<br>') || lookback.endsWith('<br/>') || lookback.endsWith('<p>')) return match
    return '<br/><br/>' + match
  })

  // Also handle lettered sub-sections (e.g., (a), (b), (i), (ii))
  formatted = formatted.replace(/\(([a-z]|i{1,3}|iv|v|vi{1,3}|ix|x)\)(?=\s+[A-Za-z])/gi, (match, _p1, offset: number, str: string) => {
    if (offset === 0) return match
    const prevChar = str[offset - 1]
    if (prevChar === '\n') return match
    const lookback = str.slice(Math.max(0, offset - 5), offset).toLowerCase()
    if (lookback.endsWith('<br>') || lookback.endsWith('<br/>') || lookback.endsWith('<p>')) return match
    return '<br/>' + match
  })

  return formatted
}

export function useContractGeneration() {
  const [prompt, setPrompt] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [contractData, setContractData] = useState<ContractData>({
    content: "",
    isComplete: false
  })
  const [error, setError] = useState<string | null>(null)
  const [formattedApplied, setFormattedApplied] = useState(false)
  const [hasStartedGenerating, setHasStartedGenerating] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const generateContract = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)
    setHasStartedGenerating(true)
    setError(null)
    setContractData({ content: "", isComplete: false })
    setFormattedApplied(false)

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

  const stopGeneration = () => {
    if (contractData.contractId) {
      fetch(`/api/contracts/${contractData.contractId}/stop`, { method: "DELETE" })
        .catch(console.error)
    }
    setIsGenerating(false)
  }

  const resetContract = () => {
    setContractData({ content: "", isComplete: false })
    setError(null)
    setHasStartedGenerating(false)
    setFormattedApplied(false)
  }

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

  // Computed value for display content with formatting applied
  const formattedDisplayContent = useMemo(() => {
    return formatClauseBreaks(contractData.content)
  }, [contractData.content])

  // Cleanup
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return {
    prompt,
    setPrompt,
    isGenerating,
    contractData: {
      ...contractData,
      content: formattedDisplayContent // Always return formatted content for display
    },
    error,
    hasStartedGenerating,
    generateContract,
    stopGeneration,
    resetContract
  }
}
