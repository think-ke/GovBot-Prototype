import type React from "react"
import { cn } from "@/lib/utils"

interface SidebarInsetProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SidebarInset({ className, ...props }: SidebarInsetProps) {
  return <div className={cn("flex flex-col flex-1", className)} {...props} />
}
