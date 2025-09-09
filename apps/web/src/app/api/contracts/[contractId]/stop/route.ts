import { auth } from "@/auth"

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ contractId: string }> }
) {
  const session = await auth()
  const { contractId } = await params
  if (!session) {
    return Response.json({"error": "Unauthorized"}, { status: 401 })
  }

  try {
    if (!contractId) {
      return Response.json({"error": "Contract ID is required"}, { status: 400 })
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
      return Response.json({"error": errorText}, { status: backendResponse.status })
    }

    const result = await backendResponse.json()
    return Response.json(result, {
      status: 200
    })
  } catch (error) {
    console.error("Stop contract error:", error)
    return Response.json({"error": "Internal server error"}, { status: 500 })
  }
} 