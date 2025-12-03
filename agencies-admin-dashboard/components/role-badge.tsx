import { Badge } from "@/components/ui/badge"
import type { UserRole } from "@/lib/auth"

type RoleBadgeProps = {
  role: UserRole
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const roleConfig: Record<UserRole, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> =
    {
      admin: { label: "Admin", variant: "destructive" },
      user: { label: "User", variant: "secondary" },
    }

  const config = roleConfig[role]

  return <Badge variant={config.variant}>{config.label}</Badge>
}
