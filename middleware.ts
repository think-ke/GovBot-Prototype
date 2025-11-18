import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const session = request.cookies.get("session")
  const isAuthPage = request.nextUrl.pathname === "/"
  const isDashboard = request.nextUrl.pathname.startsWith("/dashboard")

  // Redirect to dashboard if logged in and trying to access login page
  if (isAuthPage && session) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  // Redirect to login if not logged in and trying to access dashboard
  if (isDashboard && !session) {
    return NextResponse.redirect(new URL("/", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/", "/dashboard/:path*"],
}
