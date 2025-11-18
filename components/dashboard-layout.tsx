"use client"

import type React from "react"
import { useState } from "react"
import { Sidebar } from "./sidebar"

type DashboardLayoutProps = {
  children: React.ReactNode
  activeView: "chat" | "management"
  onViewChange: (view: "chat" | "management") => void
}

export function DashboardLayout({ children, activeView, onViewChange }: DashboardLayoutProps) {
  const [dynamicBgColor, setDynamicBgColor] = useState<string>()

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar activeView={activeView} onViewChange={onViewChange} dynamicBgColor={dynamicBgColor} />
      <main className="flex-1 overflow-hidden lg:ml-64">
        {/* {typeof children === "function" ? children({ onColorDetected: setDynamicBgColor }) : children} */}
        {children}    
         </main>
    </div>
  )
}
