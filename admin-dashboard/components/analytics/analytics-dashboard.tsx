"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ExecutiveDashboard } from "./executive-dashboard"
import { UserAnalyticsDashboard } from "./user-analytics-dashboard"
import { UsageAnalyticsDashboard } from "./usage-analytics-dashboard"
import { ConversationAnalyticsDashboard } from "./conversation-analytics-dashboard"

export type DashboardView = "executive" | "user" | "usage" | "conversation"

export function AnalyticsDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
          <p className="text-muted-foreground">
            Comprehensive insights into system performance and user interactions
          </p>
        </div>
      </div>

      <Tabs defaultValue="executive" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="executive">Executive Overview</TabsTrigger>
          <TabsTrigger value="user">User Analytics</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
          <TabsTrigger value="conversation">Conversation Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="executive" className="space-y-6">
          <ExecutiveDashboard />
        </TabsContent>

        <TabsContent value="user" className="space-y-6">
          <UserAnalyticsDashboard />
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          <UsageAnalyticsDashboard />
        </TabsContent>

        <TabsContent value="conversation" className="space-y-6">
          <ConversationAnalyticsDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}
