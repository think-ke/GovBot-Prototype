import { redirect } from "next/navigation"
import { getSession } from "@/lib/auth"
import type React from "react"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getSession()

  if (!session) {
    redirect("/")
  }

  return <>{children}</>
}
