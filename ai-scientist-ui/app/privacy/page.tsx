// app/privacy/page.tsx
import Link from "next/link"
import { Dna } from "lucide-react"

export const metadata = {
  title: "Privacy Policy — AI Scientist",
  description: "Privacy Policy for AI Scientist Drug Discovery Platform",
}

const LAST_UPDATED = "April 6, 2026"
const COMPANY      = "AI Scientist"
const EMAIL        = "privacy@aiscientist.in"

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

      {/* DPDPA compliance note */}
      <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl px-5 py-4 mb-8">
        <p className="text-sm font-bold text-blue-800 mb-1">
          🔒 Your Data, Your Rights
        </p>
        <p className="text-sm text-blue-700 leading-relaxed">
          This policy complies with India's Digital Personal Data Protection Act
          (DPDPA) 2023. We do not process sensitive personal data or patient
          health information. You can request deletion of your data at any time.
        </p>
      </div>

      <div className="prose prose-sm max-w-none">
        <h1 className="text-2xl font-black text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-400 mb-8">Last updated: {LAST_UPDATED}</p>

        <Section title="1. Who We Are">
          <p>
            {COMPANY} operates an AI-powered drug discovery research platform.
            This Privacy Policy explains how we collect, use, store, and protect
            your personal data when you use our services at aiscientist.in.
          </p>
          <p>
            We are the Data Fiduciary as defined under India's Digital Personal
            Data Protection Act (DPDPA) 2023.
          </p>
        </Section>

        <Section title="2. Data We Collect">
          <p><strong>Account Data (provided by you):</strong></p>
          <ul>
            <li>Full name and email address</li>
            <li>Password (stored as bcrypt hash — never plain text)</li>
            <li>Organization name and billing email</li>
            <li>GSTIN (if provided for invoice purposes)</li>
          </ul>
          <p><strong>Usage Data (collected automatically):</strong></p>
          <ul>
            <li>Disease names you analyze (for caching and knowledge graph)</li>
            <li>Analysis results and hypothesis outputs</li>
            <li>Feature usage patterns (which tabs are used)</li>
            <li>API request logs (IP address, timestamp, endpoint)</li>
          </ul>
          <p><strong>Payment Data:</strong></p>
          <ul>
            <li>
              Payment transactions are processed by Razorpay. We store only the
              order ID, payment ID, amount, and plan purchased. We never store
              card numbers, UPI IDs, or bank account details.
            </li>
          </ul>
          <p><strong>What we do NOT collect:</strong></p>
          <ul>
            <li>Patient health information or clinical data</li>
            <li>Biometric or genetic data</li>
            <li>Government ID numbers (Aadhaar, PAN)</li>
            <li>Real-time location data</li>
          </ul>
        </Section>

        <Section title="3. How We Use Your Data">
          <p>We use your data to:</p>
          <ul>
            <li>Provide and improve the AI Scientist platform</li>
            <li>Process payments and manage subscriptions</li>
            <li>Send transactional emails (verification, invoices, password reset)</li>
            <li>Cache analysis results to improve performance</li>
            <li>Build the cross-disease knowledge graph (disease names only)</li>
            <li>Detect and prevent fraud or abuse</li>
            <li>Comply with legal obligations</li>
          </ul>
          <p>
            We do <strong>not</strong> use your data for advertising, sell it to
            third parties, or use it to train AI models without your explicit consent.
          </p>
        </Section>

        <Section title="4. Legal Basis for Processing (DPDPA)">
          <p>
            Under India's Digital Personal Data Protection Act 2023, we process
            your personal data based on:
          </p>
          <ul>
            <li>
              <strong>Consent:</strong> You provide explicit consent when creating
              an account and agreeing to these terms
            </li>
            <li>
              <strong>Contractual necessity:</strong> Processing required to
              provide the service you subscribed to
            </li>
            <li>
              <strong>Legal obligation:</strong> Compliance with tax laws,
              financial regulations
            </li>
          </ul>
        </Section>

        <Section title="5. Data Sharing">
          <p>
            We share your data only with these trusted third-party services
            necessary to operate the platform:
          </p>
          <ul>
            <li>
              <strong>Neon (PostgreSQL):</strong> Database hosting — stores
              account and analysis data (US servers)
            </li>
            <li>
              <strong>Vercel:</strong> Frontend hosting and CDN (global)
            </li>
            <li>
              <strong>Render:</strong> Backend API hosting (US servers)
            </li>
            <li>
              <strong>Razorpay:</strong> Payment processing (India servers,
              RBI regulated)
            </li>
            <li>
              <strong>Resend:</strong> Transactional email delivery
            </li>
            <li>
              <strong>OpenAI:</strong> Disease name and research context sent
              for hypothesis generation (no personal data sent)
            </li>
          </ul>
          <p>
            We do not share your data with advertising networks, data brokers,
            or any parties not listed above.
          </p>
        </Section>

        <Section title="6. Data Retention">
          <ul>
            <li>
              <strong>Account data:</strong> Retained while your account is
              active and for 30 days after deletion
            </li>
            <li>
              <strong>Analysis results:</strong> Retained for the duration of
              your subscription
            </li>
            <li>
              <strong>Payment records:</strong> Retained for 7 years as required
              by Indian tax law (GST compliance)
            </li>
            <li>
              <strong>API logs:</strong> Retained for 90 days for security
              and debugging purposes
            </li>
          </ul>
        </Section>

        <Section title="7. Your Rights (DPDPA 2023)">
          <p>Under India's DPDPA, you have the right to:</p>
          <ul>
            <li>
              <strong>Access:</strong> Request a copy of all personal data we
              hold about you
            </li>
            <li>
              <strong>Correction:</strong> Request correction of inaccurate
              personal data
            </li>
            <li>
              <strong>Erasure:</strong> Request deletion of your personal data
              (right to be forgotten)
            </li>
            <li>
              <strong>Grievance redressal:</strong> Lodge a complaint with our
              grievance officer
            </li>
            <li>
              <strong>Withdraw consent:</strong> Withdraw consent at any time
              by deleting your account
            </li>
          </ul>
          <p>
            To exercise these rights, contact us at{" "}
            <a href={`mailto:${EMAIL}`} className="text-blue-600 hover:text-blue-800">
              {EMAIL}
            </a>{" "}
            or use the Delete Account feature in your Profile settings.
            We will respond within 72 hours.
          </p>
        </Section>

        <Section title="8. Cookies">
          <p>We use the following cookies:</p>
          <ul>
            <li>
              <strong>Session cookies:</strong> Essential for authentication
              (next-auth.session-token) — cannot be disabled
            </li>
            <li>
              <strong>CSRF token:</strong> Security cookie to prevent
              cross-site request forgery
            </li>
            <li>
              <strong>Preference cookies:</strong> Remember your cookie consent
              choice (cookie_consent)
            </li>
          </ul>
          <p>
            We do not use advertising cookies, tracking pixels, or third-party
            analytics cookies. See our{" "}
            <Link href="/cookies" className="text-blue-600 hover:text-blue-800">
              Cookie Policy
            </Link>{" "}
            for details.
          </p>
        </Section>

        <Section title="9. Data Security">
          <p>We protect your data using:</p>
          <ul>
            <li>TLS/HTTPS encryption for all data in transit</li>
            <li>bcrypt hashing for passwords (cost factor 12)</li>
            <li>Row-level security on database access</li>
            <li>JWT tokens with short expiry for sessions</li>
            <li>API rate limiting to prevent abuse</li>
          </ul>
          <p>
            In the event of a data breach affecting your personal data, we will
            notify you within 72 hours as required by DPDPA 2023.
          </p>
        </Section>

        <Section title="10. International Data Transfers">
          <p>
            Your data may be processed on servers located outside India
            (primarily US-based infrastructure via Vercel, Render, and Neon).
            By using our service, you consent to this transfer. We ensure
            adequate protection through contractual safeguards with our
            service providers.
          </p>
        </Section>

        <Section title="11. Children's Privacy">
          <p>
            Our service is not directed to individuals under the age of 18.
            We do not knowingly collect personal data from minors. If you
            believe we have inadvertently collected data from a minor, please
            contact us immediately for deletion.
          </p>
        </Section>

        <Section title="12. Grievance Officer">
          <p>
            As required by DPDPA 2023, you may contact our Grievance Officer
            for any privacy-related complaints:
          </p>
          <div className="bg-gray-50 rounded-lg p-4 text-sm">
            <p><strong>Grievance Officer:</strong> AI Scientist Privacy Team</p>
            <p><strong>Email:</strong>{" "}
              <a href={`mailto:${EMAIL}`} className="text-blue-600">{EMAIL}</a>
            </p>
            <p><strong>Response time:</strong> Within 72 hours</p>
            <p><strong>Resolution time:</strong> Within 30 days</p>
          </div>
        </Section>

        <Section title="13. Changes to This Policy">
          <p>
            We may update this Privacy Policy periodically. We will notify you
            of material changes via email and by updating the "Last updated" date.
            Continued use of the service after changes constitutes acceptance
            of the updated policy.
          </p>
        </Section>

        <Section title="14. Contact Us">
          <p>
            For privacy-related questions or to exercise your rights:{" "}
            <a href={`mailto:${EMAIL}`} className="text-blue-600 hover:text-blue-800">
              {EMAIL}
            </a>
          </p>
        </Section>
      </div>

      {/* Footer nav */}
      <div className="mt-12 pt-6 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <Link href="/terms" className="hover:text-gray-600">Terms of Service</Link>
          <Link href="/"      className="hover:text-gray-600">← Back to App</Link>
        </div>
        <p className="text-xs text-gray-300">
          © {new Date().getFullYear()} {COMPANY}
        </p>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-base font-bold text-gray-900 mb-3 pb-2 border-b border-gray-100">
        {title}
      </h2>
      <div className="text-sm text-gray-600 leading-relaxed space-y-3">
        {children}
      </div>
    </div>
  )
}