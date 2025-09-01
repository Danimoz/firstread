import { auth } from "@/auth"
import { NextRequest } from "next/server"

export async function DELETE(
  request: NextRequest,
  { params }: { params: { contractId: string } }
) {
  const session = await auth()

  if (!session) {
    return new Response("Unauthorized", { status: 401 })
  }

  try {
    const { contractId } = params

    if (!contractId) {
      return new Response("Contract ID is required", { status: 400 })
    }

    // Forward the request to the backend API
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL
    const backendResponse = await fetch(`${apiUrl}/contracts/${contractId}/stop`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${session.accessToken}`
      }
    })

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      return new Response(errorText, { status: backendResponse.status })
    }

    const result = await backendResponse.json()
    return new Response(JSON.stringify(result), {
      status: 200,
      headers: {
        "Content-Type": "application/json"
      }
    })
  } catch (error) {
    console.error("Stop contract error:", error)
    return new Response("Internal server error", { status: 500 })
  }
} 