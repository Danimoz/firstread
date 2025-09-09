"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ContractLLMEditor } from "@/components/contract-llm-editor"
import { useContractEditor } from "@/hooks/use-contract-editor"
import { Card, CardContent } from "@/components/ui/card"

interface Contract {
  id: string
  title: string
  content: string
  status: string
}

interface EditContractPageProps {
  params: {
    contractId: string
  }
}

export default function EditContractPage({ params }: EditContractPageProps) {
  const router = useRouter()
  const { isLoading, error, getContract } = useContractEditor()
  const [contract, setContract] = useState<Contract | null>(null)
  const [initialLoading, setInitialLoading] = useState(true)

  useEffect(() => {
    const loadContract = async () => {
      const { contractId } = await params
      try {
        const contractData = await getContract(contractId)
        setContract(contractData)
      } catch (err) {
        console.error("Failed to load contract:", err)
      } finally {
        setInitialLoading(false)
      }
    }

    loadContract()
  }, [params, getContract])

  const handleEditComplete = (newContractId: string) => {
    // Redirect to the new edited contract
    router.push(`/contracts/${newContractId}`)
  }

  const handleCancel = () => {
    router.back()
  }

  if (initialLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading contract...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <button 
                onClick={() => router.back()}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Go Back
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-gray-600 mb-4">Contract not found</p>
              <button 
                onClick={() => router.back()}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Go Back
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <ContractLLMEditor
      contractId={contract.id}
      initialTitle={contract.title}
      initialContent={contract.content}
      onEditComplete={handleEditComplete}
      onCancel={handleCancel}
    />
  )
}
