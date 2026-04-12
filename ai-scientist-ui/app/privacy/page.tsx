// app/privacy/page.tsx — Global privacy policy (GDPR + CCPA + international)
import Link from "next/link"
import { Dna } from "lucide-react"

export const metadata = {
  title: "Privacy Policy — Causyn AI",
  description: "Privacy Policy for Causyn AI Drug Discovery Platform",
}

const LAST_UPDATED = "April 12, 2026"
const COMPANY      = "Causyn AI"
const EMAIL        = "privacy@causyn.ai"
const WEBSITE      = "https://causyn.ai"

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-base font-bold text-gray-900 mb-3 pb-2 border-b border-gray-100">{title}</h2>
      <div className="text-sm text-gray-600 leading-relaxed space-y-3">{children}</div>
    </div>
  )
}

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto py-8 px-4">

      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center">
          <Dna className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-gray-900">{COMPANY}</p>
          <p className="text-xs text-gray-400">Privacy Policy</p>
        </div>
      </div>

      {/* Compliance banner */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl px-5 py-4 mb-8">
        <p className="text-sm font-bold text-blue-800 mb-1">
          🔒 Your Privacy Rights — Global Coverage
        </p>
        <p className="text-sm text-blue-700 leading-relaxed">
          This policy complies with the EU General Data Protection Regulation (GDPR),
          California Consumer Privacy Act (CCPA), and applicable international data
          protection laws. We do not process sensitive personal health information
          or patient data. You can request deletion of your data at any time by
          contacting {EMAIL}.
        </p>
      </div>

      <div className="prose prose-sm max-w-none">
        <h1 className="text-2xl font-black text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-400 mb-8">Last updated: {LAST_UPDATED}</p>

        <Section title="1. Who We Are">
          <p>
            {COMPANY} operates an AI-powered drug discovery research platform accessible at {WEBSITE}.
            This Privacy Policy explains how we collect, use, store, and protect your personal
            data when you use our services.
          </p>
          <p>
            We are committed to protecting your privacy and handling your data in an open and
            transparent manner. This policy applies to all users worldwide.
          </p>
        </Section>

        <Section title="2. Data We Collect">
          <p><strong>Account Information:</strong> Name, email address, and password (hashed) when you register.</p>
          <p><strong>Usage Data:</strong> Disease names analyzed, analysis results, timestamps, and feature usage patterns.</p>
          <p><strong>Payment Data:</strong> Billing information is processed by our payment processor (Stripe). We store only the last 4 digits of your card and billing address. We never store full card details.</p>
          <p><strong>Technical Data:</strong> IP address, browser type, device information, and cookies for session management and security.</p>
          <p><strong>Communications:</strong> Emails you send to our support team.</p>
          <p>
            <strong>We do NOT collect:</strong> Patient health data, clinical records, genetic sequences, or any sensitive personal health information.
            Our platform analyzes publicly available scientific databases only.
          </p>
        </Section>

        <Section title="3. How We Use Your Data">
          <p>We use your data to:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Provide, maintain, and improve our platform</li>
            <li>Process payments and send billing receipts</li>
            <li>Send important account and security notifications</li>
            <li>Respond to your support requests</li>
            <li>Analyze usage patterns to improve our services (anonymized)</li>
            <li>Comply with legal obligations</li>
          </ul>
          <p>We do not sell, rent, or share your personal data with third parties for marketing purposes.</p>
        </Section>

        <Section title="4. Legal Basis for Processing (GDPR)">
          <p>For users in the European Economic Area (EEA), we process your data under the following legal bases:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>Contract performance:</strong> Processing necessary to provide our services</li>
            <li><strong>Legitimate interests:</strong> Security, fraud prevention, and service improvement</li>
            <li><strong>Legal obligation:</strong> Compliance with applicable laws</li>
            <li><strong>Consent:</strong> Marketing communications (you can withdraw at any time)</li>
          </ul>
        </Section>

        <Section title="5. Data Storage & Security">
          <p>
            Your data is stored on secure servers in the United States (Neon PostgreSQL, hosted on AWS).
            We use industry-standard encryption (TLS 1.3) for data in transit and AES-256 encryption
            for sensitive data at rest.
          </p>
          <p>
            We implement access controls, regular security audits, and monitoring to protect your data
            from unauthorized access, alteration, or disclosure.
          </p>
          <p>
            In the event of a data breach that affects your personal data, we will notify you within
            72 hours as required by GDPR.
          </p>
        </Section>

        <Section title="6. International Data Transfers">
          <p>
            Your data may be transferred to and processed in countries outside your home country,
            including the United States. We ensure appropriate safeguards are in place for such
            transfers, including Standard Contractual Clauses (SCCs) approved by the European Commission
            for transfers from the EEA.
          </p>
        </Section>

        <Section title="7. Data Retention">
          <p>We retain your personal data for as long as:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Your account is active</li>
            <li>Necessary to provide our services</li>
            <li>Required by applicable law (typically 7 years for financial records)</li>
          </ul>
          <p>
            When you delete your account, we delete your personal data within 30 days,
            except where retention is required by law.
          </p>
        </Section>

        <Section title="8. Your Rights">
          <p>Depending on your location, you have the following rights:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>Access:</strong> Request a copy of your personal data</li>
            <li><strong>Rectification:</strong> Correct inaccurate personal data</li>
            <li><strong>Erasure:</strong> Request deletion of your personal data ("right to be forgotten")</li>
            <li><strong>Restriction:</strong> Request we limit how we process your data</li>
            <li><strong>Portability:</strong> Receive your data in a machine-readable format</li>
            <li><strong>Object:</strong> Object to processing based on legitimate interests</li>
            <li><strong>Withdraw consent:</strong> Withdraw consent at any time where processing is based on consent</li>
          </ul>
          <p>
            <strong>California residents (CCPA):</strong> You have the right to know what personal information
            we collect, the right to delete, and the right to opt out of sale (we do not sell personal data).
          </p>
          <p>
            To exercise any of these rights, contact us at <strong>{EMAIL}</strong>.
            We will respond within 30 days.
          </p>
        </Section>

        <Section title="9. Cookies">
          <p>We use the following cookies:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>Essential cookies:</strong> Required for authentication and security (cannot be disabled)</li>
            <li><strong>Analytics cookies:</strong> Help us understand how users interact with our platform (can be disabled)</li>
          </ul>
          <p>We do not use advertising or tracking cookies.</p>
        </Section>

        <Section title="10. Third-Party Services">
          <p>We use the following third-party services that may process your data:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li><strong>Stripe:</strong> Payment processing (PCI-DSS Level 1 compliant)</li>
            <li><strong>Resend:</strong> Transactional emails</li>
            <li><strong>Vercel:</strong> Frontend hosting</li>
            <li><strong>Neon / AWS:</strong> Database hosting</li>
            <li><strong>OpenAI:</strong> AI model inference (analysis queries only — no personal data sent)</li>
          </ul>
          <p>Each of these providers has their own privacy policy and data processing agreements with us.</p>
        </Section>

        <Section title="11. Children's Privacy">
          <p>
            Our platform is not directed to individuals under the age of 18.
            We do not knowingly collect personal data from children.
            If you believe we have inadvertently collected data from a minor,
            please contact us immediately at {EMAIL}.
          </p>
        </Section>

        <Section title="12. Changes to This Policy">
          <p>
            We may update this Privacy Policy from time to time. We will notify you of
            significant changes by email or by displaying a prominent notice on our platform.
            Your continued use of the platform after changes constitutes acceptance of the updated policy.
          </p>
        </Section>

        <Section title="13. Contact & Complaints">
          <p>
            For privacy questions or to exercise your rights, contact our Privacy Team at:
          </p>
          <div className="bg-gray-50 rounded-xl p-4 mt-2">
            <p><strong>Causyn AI — Privacy Team</strong></p>
            <p>Email: <a href={`mailto:${EMAIL}`} className="text-blue-600">{EMAIL}</a></p>
            <p>Website: <a href={WEBSITE} className="text-blue-600">{WEBSITE}</a></p>
          </div>
          <p className="mt-3">
            If you are in the EU and believe we have not handled your data correctly,
            you have the right to lodge a complaint with your local data protection authority.
          </p>
        </Section>
      </div>

      {/* Footer links */}
      <div className="mt-10 pt-6 border-t border-gray-100 flex items-center justify-between">
        <Link href="/terms"   className="text-sm text-blue-600 hover:text-blue-800">Terms of Service →</Link>
        <Link href="/"        className="text-sm text-gray-400 hover:text-gray-600">← Back to Dashboard</Link>
      </div>
    </div>
  )
}