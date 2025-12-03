"use client"

import { useState } from "react"
import { MessageSquare, LayoutDashboard, LogOut, Menu, X, Mail, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/auth-context"
import { logout } from "@/lib/auth"
import { hasRole } from "@/lib/permissions"
import { useRouter } from "next/navigation"
import { SupportFeedbackModal } from "@/components/support-feedback-modal"
import { RoleManagementModal } from "@/components/role-management-modal"
import { RoleBadge } from "@/components/role-badge"

type SidebarProps = {
  activeView: "chat" | "management"
  onViewChange: (view: "chat" | "management") => void
  dynamicBgColor?: string
}

export function Sidebar({ activeView, onViewChange, dynamicBgColor }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false)
  const [isRoleManagementOpen, setIsRoleManagementOpen] = useState(false)
  const { user, setUser } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    setUser(null)
    router.push("/")
    router.refresh()
  }

  const menuItems = hasRole(user, "admin")
    ? [
        {
          id: "management" as const,
          label: "Management",
          icon: LayoutDashboard,
          description: "Dashboard",
        },
      ]
    : [
        {
          id: "chat" as const,
          label: "Chat",
          icon: MessageSquare,
          description: "Chat Interface",
        },
      ]

  const sidebarStyle = dynamicBgColor ? { backgroundColor: dynamicBgColor } : {}

  return (
    <>
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </Button>

      {/* Sidebar */}
      <aside
        style={sidebarStyle}
        className={cn(
          "fixed left-0 top-0 z-40 h-screen w-64 border-r border-sidebar-border transition-colors duration-500 ease-in-out lg:translate-x-0",
          !dynamicBgColor && "bg-sidebar",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center border-b border-sidebar-border px-6">
            <h1 className="text-xl font-semibold text-sidebar-foreground">GovBot Portal</h1>
          </div>

          {/* User info */}
          <div className="border-b border-sidebar-border px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground">
                {user?.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sidebar-foreground truncate">{user?.name}</p>
                <p className="text-xs text-sidebar-foreground/60 truncate">{user?.email}</p>
                {user && <RoleBadge role={user.role} />}
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = activeView === item.id

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onViewChange(item.id)
                    setIsOpen(false)
                  }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <div className="flex flex-col items-start">
                    <span>{item.label}</span>
                    <span className="text-xs opacity-60">{item.description}</span>
                  </div>
                </button>
              )
            })}
          </nav>

          {hasRole(user, "admin") && (
            <div className="border-t border-sidebar-border px-4 py-3">
              <button
                onClick={() => setIsRoleManagementOpen(true)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors"
              >
                <Users className="h-4 w-4" />
                <div className="flex flex-col items-start">
                  <span className="text-xs font-medium">Manage Roles</span>
                  <span className="text-xs opacity-60">Admin only</span>
                </div>
              </button>
            </div>
          )}

          {/* Support email section */}
          <div className="border-t border-sidebar-border px-4 py-3">
            <button
              onClick={() => setIsFeedbackOpen(true)}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors"
            >
              <Mail className="h-4 w-4" />
              <div className="flex flex-col items-start">
                <span className="text-xs font-medium">Support</span>
                <span className="text-xs opacity-60">support@think.ke</span>
              </div>
            </button>
          </div>

          {/* Logout button */}
          <div className="border-t border-sidebar-border p-4">
            <Button
              variant="ghost"
              className="w-full justify-start text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
              onClick={handleLogout}
            >
              <LogOut className="mr-3 h-5 w-5" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setIsOpen(false)} aria-hidden="true" />
      )}

      {/* Support Feedback Modal */}
      <SupportFeedbackModal isOpen={isFeedbackOpen} onClose={() => setIsFeedbackOpen(false)} />

      <RoleManagementModal
        isOpen={isRoleManagementOpen}
        onClose={() => setIsRoleManagementOpen(false)}
        currentUser={user}
      />
    </>
  )
}
