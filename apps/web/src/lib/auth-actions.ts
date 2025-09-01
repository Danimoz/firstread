"use server"

import { signIn } from "@/auth"
import { redirect } from "next/navigation"

export async function registerUser(formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  try {
    // Use API_URL for server-side requests (container-to-container)
    // Use NEXT_PUBLIC_API_URL for client-side requests (browser-to-container)
    const apiUrl = process.env.API_URL
    const res = await fetch(`${apiUrl}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    })

    if (!res.ok) {
      const errorData = await res.text()
      return { error: errorData || "Failed to register user" }
    }

    const userData = await res.json()

    // If registration is successful, try to sign in the user
    if (userData.access_token || res.status === 201) {
      try {
        const result = await signIn("credentials", {
          email,
          password,
          redirect: false
        })

        if (result?.error) {
          // Registration successful but login failed - user can login manually
          return { success: "Account created successfully! Please sign in." }
        }

        // Both registration and login successful
        redirect("/")
      } catch (signInError) {
        // Registration successful but login failed - user can login manually
        return { success: "Account created successfully! Please sign in." }
      }
    }

    return { success: "User registered successfully" }
  } catch (error) {
    console.error("Registration error:", error)
    return { error: "An unexpected error occurred during registration" }
  }
}

export async function loginUser(formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  try {
    const result = await signIn("credentials", {
      email,
      password,
      redirect: false
    })

    if (result?.error) {
      return { error: "Invalid email or password" }
    }
  } catch (error) {
    console.error("Login error:", error)
    return { error: "An unexpected error occurred during login" }
  }
  
  redirect("/")
} 