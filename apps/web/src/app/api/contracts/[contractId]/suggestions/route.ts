import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ contractId: string }> }
) {
  try {
    const { contractId } = await params

    // Get auth token from cookies
    const token = request.cookies.get("access_token")?.value

    if (!token) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const response = await fetch(`${API_BASE_URL}/contracts/${contractId}/suggestions`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: errorData || "Failed to get suggestions" },
        { status: response.status }
      )
    }

    const suggestions = await response.json()
    return NextResponse.json(suggestions)
  } catch (error) {
    console.error("Error getting suggestions:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
