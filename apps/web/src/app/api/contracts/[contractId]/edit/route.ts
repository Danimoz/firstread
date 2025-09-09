import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ contractId: string }> }
) {
  try {
    const { contractId } = await params
    const body = await request.json()

    // Get auth token from cookies
    const token = request.cookies.get("access_token")?.value

    if (!token) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const response = await fetch(`${API_BASE_URL}/contracts/${contractId}/edit`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: errorData || "Failed to edit contract" },
        { status: response.status }
      )
    }

    // Return the streaming response directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error("Error editing contract:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
