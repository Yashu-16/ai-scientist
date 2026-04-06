// lib/email.ts
import { Resend } from "resend"

const resend = new Resend(process.env.RESEND_API_KEY ?? "re_placeholder")
const FROM   = process.env.EMAIL_FROM ?? "onboarding@resend.dev"
const APP    = process.env.NEXTAUTH_URL ?? "http://localhost:3000"

export async function sendVerificationEmail(
  email: string, name: string, token: string
) {
  const url = `${APP}/api/auth/verify?token=${token}`

  try {
    await resend.emails.send({
      from:    FROM,
      to:      email,
      subject: "Verify your AI Scientist account",
      html: `
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;">
          <h2 style="color:#1e293b">Welcome to AI Scientist, ${name}!</h2>
          <p style="color:#475569;line-height:1.6">
            You're one step away from unlocking AI-powered drug discovery.
            Click the button below to verify your email address.
          </p>
          <a href="${url}" style="display:inline-block;margin:24px 0;padding:12px 28px;
            background:#2563eb;color:white;text-decoration:none;border-radius:8px;font-weight:600;">
            Verify Email Address
          </a>
          <p style="color:#94a3b8;font-size:13px;">
            This link expires in 24 hours. If you didn't sign up, ignore this email.
          </p>
          <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0"/>
          <p style="color:#94a3b8;font-size:12px;">
            AI Scientist · For exploratory research only · Not for clinical use
          </p>
        </div>
      `
    })
  } catch (error) {
    console.error("Failed to send verification email:", error)
  }
}

export async function sendPasswordResetEmail(
  email: string, name: string, token: string
) {
  const url = `${APP}/auth/reset-password?token=${token}`

  try {
    await resend.emails.send({
      from:    FROM,
      to:      email,
      subject: "Reset your AI Scientist password",
      html: `
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;">
          <h2 style="color:#1e293b">Password Reset</h2>
          <p style="color:#475569;line-height:1.6">
            Hi ${name}, we received a request to reset your password.
            Click below to choose a new one.
          </p>
          <a href="${url}" style="display:inline-block;margin:24px 0;padding:12px 28px;
            background:#2563eb;color:white;text-decoration:none;border-radius:8px;font-weight:600;">
            Reset Password
          </a>
          <p style="color:#94a3b8;font-size:13px;">
            This link expires in 1 hour. If you didn't request this, ignore this email.
          </p>
        </div>
      `
    })
  } catch (error) {
    console.error("Failed to send reset email:", error)
  }
}
export async function sendOrgInviteEmail(
  email: string,
  orgName: string,
  inviterName: string,
  role: string,
  token: string
) {
  const url = `${APP}/org/invite/accept?token=${token}`

  try {
    await resend.emails.send({
      from:    FROM,
      to:      email,
      subject: `You've been invited to join ${orgName} on AI Scientist`,
      html: `
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;">
          <h2 style="color:#1e293b">You're invited!</h2>
          <p style="color:#475569;line-height:1.6">
            <strong>${inviterName}</strong> has invited you to join
            <strong>${orgName}</strong> on AI Scientist as a <strong>${role}</strong>.
          </p>
          <a href="${url}" style="display:inline-block;margin:24px 0;padding:12px 28px;
            background:#2563eb;color:white;text-decoration:none;border-radius:8px;font-weight:600;">
            Accept Invitation
          </a>
          <p style="color:#94a3b8;font-size:13px;">
            This invitation expires in 7 days. If you don't have an account,
            you'll be asked to create one first.
          </p>
        </div>
      `
    })
  } catch (error) {
    console.error("Failed to send invite email:", error)
  }
}