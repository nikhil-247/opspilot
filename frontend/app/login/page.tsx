"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight } from "lucide-react";
import { FormEvent, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign-in failed");
      router.replace("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link href="/login" className="brand auth-brand">
          <span className="brand-icon"><Activity size={21} /></span>
          <span>OpsPilot<small>INCIDENT OPERATIONS</small></span>
        </Link>
        <div className="auth-heading">
          <span className="eyebrow">WELCOME BACK</span>
          <h1>Sign in to your workspace</h1>
          <p>Continue monitoring incidents and keeping services healthy.</p>
        </div>
        <form onSubmit={submit} className="form-stack">
          <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required autoComplete="email" /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" required autoComplete="current-password" /></label>
          {error && <div className="form-error">{error}</div>}
          <button className="button button-primary button-wide" disabled={busy}>{busy ? "Signing in…" : "Sign in"} <ArrowRight size={16} /></button>
        </form>
        <div className="auth-switch">New to OpsPilot? <Link href="/register">Create a workspace</Link></div>
      </section>
    </main>
  );
}
