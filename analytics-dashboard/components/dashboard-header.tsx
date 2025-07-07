import { Bell, Download, RefreshCw, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type { DashboardView } from "@/app/page"
import { SidebarTrigger } from "@/components/ui/sidebar"

interface DashboardHeaderProps {
  activeView: DashboardView
}

const viewTitles = {
  executive: "Executive Overview",
  user: "User Analytics",
  usage: "Usage Analytics",
  conversation: "Conversation Analytics",
}

const viewDescriptions = {
  executive: "High-level KPIs and strategic insights for leadership decision-making",
  user: "Citizen demographics, behavior patterns, and satisfaction metrics",
  usage: "System performance, traffic patterns, and operational health monitoring",
  conversation: "Dialog analysis, intent patterns, and content effectiveness",
}

export function DashboardHeader({ activeView }: DashboardHeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900">{viewTitles[activeView]}</h1>
              <Badge variant="secondary" className="bg-emerald-100 text-emerald-800">
                Live Data
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mt-1">{viewDescriptions[activeView]}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Calendar className="w-4 h-4 mr-2" />
            Last 30 days
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Bell className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
