import { auth } from "@/auth"
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const session = await auth()

  if (!session) {
    return new Response("Unauthorized", { status: 401 })
  }

  try {
    const { prompt } = await request.json()

    if (!prompt) {
      return new Response("Prompt is required", { status: 400 })
    }

    // Forward the request to the backend API
    const apiUrl = process.env.API_URL
    const backendResponse = await fetch(`${apiUrl}/contracts/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session.accessToken}`
      },
      body: JSON.stringify({ prompt })
    })

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      return new Response(errorText, { status: backendResponse.status })
    }

    // Return the streaming response from the backend
    return new Response(backendResponse.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Cache-Control"
      }
    })
  } catch (error) {
    console.error("Contract generation error:", error)
    return new Response("Internal server error", { status: 500 })
  }
} 