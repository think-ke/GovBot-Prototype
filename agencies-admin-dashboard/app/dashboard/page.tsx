"use client"

import { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard-layout"
import { IframeViewer } from "@/components/iframe-viewer"
import { useAuth } from "@/contexts/auth-context"
import { hasRole } from "@/lib/permissions"

const IFRAME_URLS = {
  chat: "https://govstack-demo.think.ke",
  management: "https://govstack-dashboard.think.ke/",
} as const

export default function DashboardPage() {
  const [activeView, setActiveView] = useState<"chat" | "management">("chat")
  const [dynamicBgColor, setDynamicBgColor] = useState<string>()
  const { user } = useAuth()

  useEffect(() => {
    if (user) {
      if (hasRole(user, "admin")) {
        setActiveView("management")
      } else if (hasRole(user, "user")) {
        setActiveView("chat")
      }
    }
  }, [user]) // Only depend on user to avoid infinite loops

  return (
    <DashboardLayout activeView={activeView} onViewChange={setActiveView}>
      <div className="h-full w-full">
        {activeView === "chat" && hasRole(user, "user") && (
          <IframeViewer url={IFRAME_URLS.chat} title="GovBot Chat" onColorDetected={setDynamicBgColor} />
        )}
        {activeView === "management" && hasRole(user, "admin") && (
          <IframeViewer url={IFRAME_URLS.management} title="GovBot Management" onColorDetected={setDynamicBgColor} />
        )}
      </div>
    </DashboardLayout>
  )
}
