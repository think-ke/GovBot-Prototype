"use server"

import { cookies } from "next/headers"

export type UserRole = "admin" | "user"

export type Permission =
  | "view_dashboard"
  | "manage_users"
  | "manage_roles"
  | "view_reports"
  | "edit_settings"
  | "delete_content"

export type User = {
  id: string
  email: string
  name: string
  role: UserRole
  permissions: Permission[]
}

import { users } from "./users"

export async function login(
  email: string,
  password: string,
): Promise<{ success: boolean; error?: string; user?: User }> {
  const user = users.find((u) => u.email === email && u.password === password)

  if (!user) {
    return { success: false, error: "Invalid email or password" }
  }

  // Create session
  const cookieStore = await cookies()
  cookieStore.set(
    "session",
    JSON.stringify({
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      permissions: user.permissions,
    }),
    {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 1 week
    },
  )

  return {
    success: true,
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      permissions: user.permissions,
    },
  }
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete("session")
}

export async function getSession(): Promise<User | null> {
  const cookieStore = await cookies()
  const session = cookieStore.get("session")

  if (!session) {
    return null
  }

  try {
    return JSON.parse(session.value) as User
  } catch {
    return null
  }
}

