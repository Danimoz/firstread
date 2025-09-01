import { signOut } from "@/auth"
import { redirect } from "next/navigation"

export async function POST() {
  await signOut({ redirect: false })
  redirect("/")
} 