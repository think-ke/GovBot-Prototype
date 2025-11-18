// filepath: /mnt/c/Users/user/Desktop/THiNK/AI/GovStackPrototype/govstack-prototype/lib/permissions.ts
// Client-side role and permission utilities.
// Keep these separate from server-only code in `lib/auth.ts` so client components
// can import and use them without pulling in server actions.

import type { User, UserRole, Permission } from "@/lib/auth"

export const rolePermissions: Record<UserRole, Permission[]> = {
  admin: ["view_dashboard", "manage_users", "manage_roles", "view_reports", "edit_settings", "delete_content"],
  user: ["view_dashboard"],
}

export function hasPermission(user: User | null, permission: Permission): boolean {
  if (!user) return false
  return user.permissions.includes(permission)
}

export function hasRole(user: User | null, role: UserRole | UserRole[]): boolean {
  if (!user) return false
  const roles = Array.isArray(role) ? role : [role]
  return roles.includes(user.role)
}

export default { hasPermission, hasRole }
