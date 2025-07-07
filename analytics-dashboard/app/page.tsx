"use client"

import { useState } from "react"
import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { DashboardHeader } from "@/components/dashboard-header"
import { ExecutiveDashboard } from "@/components/dashboards/executive-dashboard"
import { UserAnalyticsDashboard } from "@/components/dashboards/user-analytics-dashboard"
import { UsageAnalyticsDashboard } from "@/components/dashboards/usage-analytics-dashboard"
import { ConversationAnalyticsDashboard } from "@/components/dashboards/conversation-analytics-dashboard"
import { SidebarInset } from "@/components/ui/sidebar-inset"

export type DashboardView = "executive" | "user" | "usage" | "conversation"

export default function AnalyticsDashboard() {
  const [activeView, setActiveView] = useState<DashboardView>("executive")

  const renderDashboard = () => {
    switch (activeView) {
      case "executive":
        return <ExecutiveDashboard />
      case "user":
        return <UserAnalyticsDashboard />
      case "usage":
        return <UsageAnalyticsDashboard />
      case "conversation":
        return <ConversationAnalyticsDashboard />
      default:
        return <ExecutiveDashboard />
    }
  }

  return (
    <SidebarProvider defaultOpen={true}>
      <AppSidebar activeView={activeView} onViewChange={setActiveView} />
      <SidebarInset>
        <DashboardHeader activeView={activeView} />
        <main className="flex-1 p-6 overflow-auto">{renderDashboard()}</main>
      </SidebarInset>
    </SidebarProvider>
  )
}
