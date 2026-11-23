"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight } from "lucide-react";
import { FormEvent, useState } from "react";

export default function RegisterPage() {
  const router = useRouter();
  const [organizationName, setOrganizationName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          organization_name: organizationName,
          full_name: fullName,
          email,
          password,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Workspace creation failed");
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create workspace");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card auth-card-wide">
        <Link href="/login" className="brand auth-brand">
          <span className="brand-icon"><Activity size={21} /></span>
          <span>OpsPilot<small>INCIDENT OPERATIONS</small></span>
        </Link>
        <div className="auth-heading">
          <span className="eyebrow">GET STARTED</span>
          <h1>Create your operations workspace</h1>
          <p>Your account becomes the workspace owner. You can add existing accounts to your team later.</p>
        </div>
        <form onSubmit={submit} className="form-stack">
          <label>Organization name<input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} placeholder="Acme Engineering" required minLength={2} maxLength={120} /></label>
          <label>Your name<input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" required minLength={2} maxLength={120} /></label>
          <label>Work email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required autoComplete="email" /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 12 characters" required minLength={12} autoComplete="new-password" /></label>
          {error && <div className="form-error">{error}</div>}
          <button className="button button-primary button-wide" disabled={busy}>{busy ? "Creating workspace…" : "Create workspace"} <ArrowRight size={16} /></button>
        </form>
        <div className="auth-switch">Already have an account? <Link href="/login">Sign in</Link></div>
      </section>
    </main>
  );
}
