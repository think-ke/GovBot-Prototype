"use client"

import type React from "react"

import { useState } from "react"
import { X, Send, AlertCircle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/auth-context"

type SupportFeedbackModalProps = {
  isOpen: boolean
  onClose: () => void
}

export function SupportFeedbackModal({ isOpen, onClose }: SupportFeedbackModalProps) {
  const [subject, setSubject] = useState("")
  const [message, setMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")
  const { user } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setStatus("idle")

    try {
      const response = await fetch("/api/send-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject,
          message,
          userEmail: user?.email,
          userName: user?.name,
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to send feedback")
      }

      setStatus("success")
      setSubject("")
      setMessage("")
      setTimeout(() => {
        onClose()
        setStatus("idle")
      }, 2000)
    } catch (error) {
      setStatus("error")
      setErrorMessage(error instanceof Error ? error.message : "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-40 bg-black/50" onClick={onClose} aria-hidden="true" />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold">Send Feedback</h2>
          <button
            onClick={onClose}
            className="text-foreground/60 hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Status Messages */}
          {status === "success" && (
            <div className="flex items-center gap-2 rounded-lg bg-green-50 p-3 text-green-700">
              <CheckCircle className="h-5 w-5" />
              <span className="text-sm font-medium">Feedback sent successfully!</span>
            </div>
          )}

          {status === "error" && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <span className="text-sm font-medium">{errorMessage}</span>
            </div>
          )}

          {/* Subject */}
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-foreground mb-1">
              Subject
            </label>
            <input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="What is this about?"
              required
              disabled={isLoading}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-foreground/50 focus:outline-none focus:ring-2 focus:ring-sidebar-primary disabled:opacity-50"
            />
          </div>

          {/* Message */}
          <div>
            <label htmlFor="message" className="block text-sm font-medium text-foreground mb-1">
              Message
            </label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tell us what you think..."
              required
              disabled={isLoading}
              rows={4}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-foreground/50 focus:outline-none focus:ring-2 focus:ring-sidebar-primary disabled:opacity-50 resize-none"
            />
          </div>

          {/* Footer */}
          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 bg-transparent"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !subject.trim() || !message.trim()} className="flex-1 gap-2">
              <Send className="h-4 w-4" />
              {isLoading ? "Sending..." : "Send"}
            </Button>
          </div>
        </form>
      </div>
    </>
  )
}
