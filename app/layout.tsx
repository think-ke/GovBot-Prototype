import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/contexts/auth-context"
import { getSession } from "@/lib/auth"
import { Suspense } from "react"
import "./globals.css"

export const metadata: Metadata = {
  title: "GovBot Portal",
  description: "GovBot integrated platform",
  generator: "v0.app",
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const session = await getSession()

  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <Suspense fallback={<div>Loading...</div>}>
          <AuthProvider initialUser={session}>{children}</AuthProvider>
        </Suspense>
        <Analytics />
      </body>
    </html>
  )
}
