"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import type { User, UserRole, Permission } from "@/lib/auth"
import { rolePermissions } from "@/lib/permissions"

type RoleManagementModalProps = {
  isOpen: boolean
  onClose: () => void
  currentUser: User | null
}

export function RoleManagementModal({ isOpen, onClose, currentUser }: RoleManagementModalProps) {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedRole, setSelectedRole] = useState<UserRole>("user")
  const [selectedPermissions, setSelectedPermissions] = useState<Permission[]>([])

  // Mock users list - in production, this would come from a database
  const mockUsers: User[] = [
    {
      id: "1",
      email: "admin@govbot.com",
      name: "Admin User",
      role: "admin",
      permissions: rolePermissions.admin,
    },
    {
      id: "2",
      email: "user@govbot.com",
      name: "Regular User",
      role: "user",
      permissions: rolePermissions.user,
    },
  ]

  const allPermissions: Permission[] = [
    "view_dashboard",
    "manage_users",
    "manage_roles",
    "view_reports",
    "edit_settings",
    "delete_content",
  ]

  const handleSelectUser = (user: User) => {
    setSelectedUser(user)
    setSelectedRole(user.role)
    setSelectedPermissions(user.permissions)
  }

  const handleRoleChange = (role: UserRole) => {
    setSelectedRole(role)
    setSelectedPermissions(rolePermissions[role])
  }

  const handlePermissionToggle = (permission: Permission) => {
    setSelectedPermissions((prev) =>
      prev.includes(permission) ? prev.filter((p) => p !== permission) : [...prev, permission],
    )
  }

  const handleSave = () => {
    // In production, this would make an API call to update the user
    console.log("Saving user role and permissions:", {
      userId: selectedUser?.id,
      role: selectedRole,
      permissions: selectedPermissions,
    })
    onClose()
  }

  const isAdmin = currentUser?.role === "admin"

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Role & Permission Management</DialogTitle>
          <DialogDescription>Manage user roles and permissions for the platform</DialogDescription>
        </DialogHeader>

        {!isAdmin ? (
          <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
            <p className="font-medium">Access Denied</p>
            <p className="text-sm">Only administrators can manage roles and permissions.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Users List */}
            <div>
              <h3 className="font-semibold mb-3">Select User</h3>
              <div className="grid gap-2">
                {mockUsers.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleSelectUser(user)}
                    className={`p-3 rounded-lg border-2 text-left transition-colors ${
                      selectedUser?.id === user.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{user.name}</p>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                      </div>
                      <Badge variant={user.role === "admin" ? "destructive" : "secondary"}>{user.role}</Badge>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {selectedUser && (
              <>
                {/* Role Selection */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">User Role</CardTitle>
                    <CardDescription>Select the role for this user</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(["admin", "user"] as UserRole[]).map((role) => (
                        <label key={role} className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-muted">
                          <input
                            type="radio"
                            name="role"
                            value={role}
                            checked={selectedRole === role}
                            onChange={() => handleRoleChange(role)}
                            className="w-4 h-4"
                          />
                          <div>
                            <p className="font-medium capitalize">{role}</p>
                            <p className="text-xs text-muted-foreground">
                              {role === "admin" && "Full access to all features"}
                              {role === "user" && "Can only view dashboard"}
                            </p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Permissions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Permissions</CardTitle>
                    <CardDescription>Select specific permissions for this user</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      {allPermissions.map((permission) => (
                        <label key={permission} className="flex items-center gap-2 cursor-pointer">
                          <Checkbox
                            checked={selectedPermissions.includes(permission)}
                            onCheckedChange={() => handlePermissionToggle(permission)}
                          />
                          <span className="text-sm capitalize">{permission.replace(/_/g, " ")}</span>
                        </label>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Action Buttons */}
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={onClose}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave}>Save Changes</Button>
                </div>
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
