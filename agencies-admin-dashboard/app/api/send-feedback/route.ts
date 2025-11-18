import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { subject, message, userEmail, userName } = await request.json()

    // Validate input
    if (!subject || !message || !userEmail) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 })
    }

    // Format the email body
    const emailBody = `
New Feedback from GovBot Portal

From: ${userName} (${userEmail})
Subject: ${subject}

Message:
${message}

---
This email was sent from the GovBot Portal feedback form.
    `.trim()

    // Send email using a simple fetch to a mail service
    // For production, you should use a proper email service like SendGrid, Resend, or Nodemailer
    // This is a placeholder implementation

    // For now, we'll just log it and return success
    // In production, integrate with your email service
    console.log("[v0] Feedback received:", { subject, userEmail, userName })

    // TODO: Integrate with email service (SendGrid, Resend, etc.)
    // Example with Resend (if you add it):
    // const response = await resend.emails.send({
    //   from: "noreply@think.ke",
    //   to: "support@think.ke",
    //   replyTo: userEmail,
    //   subject: `[GovBot Feedback] ${subject}`,
    //   html: emailBody,
    // })

    return NextResponse.json({ success: true, message: "Feedback sent successfully" }, { status: 200 })
  } catch (error) {
    console.error("[v0] Error sending feedback:", error)
    return NextResponse.json({ error: "Failed to send feedback" }, { status: 500 })
  }
}
