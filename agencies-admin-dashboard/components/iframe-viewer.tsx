"use client"

import { useEffect, useRef, useState } from "react"
import { Loader2, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

type IframeViewerProps = {
  url: string
  title: string
  onColorDetected?: (color: string) => void
}

export function IframeViewer({ url, title, onColorDetected }: IframeViewerProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    setIsLoading(true)
    setHasError(false)
  }, [url])

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === "BACKGROUND_COLOR" && onColorDetected) {
        onColorDetected(event.data.color)
      }
    }

    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [onColorDetected])

  const handleLoad = () => {
    setIsLoading(false)
    setHasError(false)

    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ type: "GET_BACKGROUND_COLOR" }, "*")
    }
  }

  const handleError = () => {
    setIsLoading(false)
    setHasError(true)
  }

  return (
    <div className="relative h-full w-full bg-background">
      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading {title}...</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {hasError && (
        <div className="absolute inset-0 z-10 flex items-center justify-center p-4 bg-background">
          <Alert variant="destructive" className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load {title}. The website may not allow embedding or there might be a connection issue.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Iframe */}
      <iframe
        ref={iframeRef}
        src={url}
        title={title}
        className="h-full w-full border-0"
        onLoad={handleLoad}
        onError={handleError}
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-downloads"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      />
    </div>
  )
}
