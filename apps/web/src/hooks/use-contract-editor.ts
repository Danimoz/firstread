"use client"

import { useState } from "react"

interface Contract {
  id: string
  title: string
  content: string
  status: string
}

export function useContractEditor() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateContract = async (contractId: string, title: string, content: string): Promise<Contract> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/contracts/${contractId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, content })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const updatedContract = await response.json()
      return updatedContract
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update contract"
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const createContractVersion = async (contractId: string, title: string, content: string): Promise<Contract> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/contracts/${contractId}/versions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, content })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const newVersion = await response.json()
      return newVersion
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create contract version"
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const getContract = async (contractId: string): Promise<Contract> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/contracts/${contractId}`)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const contract = await response.json()
      return contract
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch contract"
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return {
    isLoading,
    error,
    updateContract,
    createContractVersion,
    getContract
  }
}
