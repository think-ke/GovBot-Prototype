import type React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  description?: string
  trend?: "up" | "down" | "neutral"
  className?: string
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  description,
  trend,
  className,
}: MetricCardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <TrendingUp className="w-4 h-4 text-emerald-600" />
      case "down":
        return <TrendingDown className="w-4 h-4 text-red-600" />
      default:
        return <Minus className="w-4 h-4 text-gray-400" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-emerald-600 bg-emerald-50"
      case "down":
        return "text-red-600 bg-red-50"
      default:
        return "text-gray-600 bg-gray-50"
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        {icon && <div className="text-gray-400">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900 mb-1">
          {typeof value === "number" ? value.toLocaleString() : value}
        </div>
        {change !== undefined && (
          <div className="flex items-center space-x-2">
            <Badge variant="secondary" className={getTrendColor()}>
              <div className="flex items-center space-x-1">
                {getTrendIcon()}
                <span className="text-xs font-medium">
                  {change > 0 ? "+" : ""}
                  {change}%
                </span>
              </div>
            </Badge>
            {changeLabel && <span className="text-xs text-gray-500">{changeLabel}</span>}
          </div>
        )}
        {description && <p className="text-xs text-gray-500 mt-2">{description}</p>}
      </CardContent>
    </Card>
  )
}
