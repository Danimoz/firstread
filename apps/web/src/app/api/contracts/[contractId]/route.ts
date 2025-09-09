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

    const response = await fetch(`${API_BASE_URL}/contracts/${contractId}`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: errorData || "Failed to fetch contract" },
        { status: response.status }
      )
    }

    const contract = await response.json()
    return NextResponse.json(contract)
  } catch (error) {
    console.error("Error fetching contract:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

export async function PUT(
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

    const response = await fetch(`${API_BASE_URL}/contracts/${contractId}`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.text()
      return NextResponse.json(
        { error: errorData || "Failed to update contract" },
        { status: response.status }
      )
    }

    const updatedContract = await response.json()
    return NextResponse.json(updatedContract)
  } catch (error) {
    console.error("Error updating contract:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
