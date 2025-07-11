import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from "@/components/theme-provider"
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryProvider } from '@/components/react-query-provider'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'GovStack Admin Dashboard',
  description: 'Administrative interface for GovStack content management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ReactQueryProvider>
            {children}
            <Toaster />
          </ReactQueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
