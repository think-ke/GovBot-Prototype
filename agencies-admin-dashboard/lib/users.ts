// Client-side mock user data
import type { User, UserRole, Permission } from "@/lib/auth"

export const users = [
  {
    id: "1",
    email: "admin@govbot.com",
    password: "admin123",
    name: "Admin User",
    role: "admin" as UserRole,
    permissions: [
      "view_dashboard",
      "manage_users",
      "manage_roles",
      "view_reports", 
      "edit_settings",
      "delete_content",
    ] as Permission[],
  },
  {
    id: "2", 
    email: "user@govbot.com",
    password: "user123",
    name: "Regular User",
    role: "user" as UserRole,
    permissions: ["view_dashboard"] as Permission[],
  },
]

export default users