"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, BrainCircuit, CheckCircle2, Clock3, RefreshCw } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch, formatDate } from "@/lib/api";
import type { Activity, Incident } from "@/lib/types";

type Analysis = {
  summary: string;
  anomaly: { detected: boolean; current_window_events: number; baseline_mean: number; z_score: number; window_minutes: number };
  hypotheses: Array<{ type: string; title: string; confidence: string; evidence: string[]; caveat: string }>;
  limitations: string[];
};

export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [incident, setIncident] = useState<Incident | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [item, timeline] = await Promise.all([
        apiFetch<Incident>("/api/v1/incidents/" + id),
        apiFetch<Activity[]>("/api/v1/incidents/" + id + "/activity"),
      ]);
      setIncident(item);
      setActivity(timeline);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load incident");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [id]);

  async function changeStatus(action: "acknowledge" | "resolve") {
    setBusy(true);
    setError("");
    try {
      await apiFetch<Incident>("/api/v1/incidents/" + id + "/" + action, {
        method: "POST",
        body: JSON.stringify({
          actor: "current-user",
          note: action === "acknowledge"
            ? "Acknowledged from OpsPilot console"
            : "Resolved from OpsPilot console",
        }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function runAnalysis() {
    setBusy(true);
    setError("");
    try {
      setAnalysis(await apiFetch<Analysis>("/api/v1/incidents/" + id + "/analysis"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Incident detail" description="Investigate event history, response activity and supporting evidence.">
      <Link href="/dashboard" className="back-link"><ArrowLeft size={15} /> Back to incidents</Link>
      {error && <div className="inline-error">{error}</div>}
      {loading ? <div className="panel empty-state">Loading incident…</div> : !incident ? <div className="panel empty-state">Incident not found in this workspace.</div> : (
        <>
          <section className="panel incident-hero">
            <div className="incident-title-row">
              <div><span className={"priority priority-" + incident.priority.toLowerCase()}>{incident.priority}</span><span className={"status status-" + incident.status}>{incident.status}</span></div>
              <div className="action-row">
                {incident.status === "open" && <button className="button button-secondary" disabled={busy} onClick={() => changeStatus("acknowledge")}><Clock3 size={15} /> Acknowledge</button>}
                {incident.status !== "resolved" && <button className="button button-primary" disabled={busy} onClick={() => changeStatus("resolve")}><CheckCircle2 size={15} /> Resolve</button>}
              </div>
            </div>
            <h2>{incident.title}</h2>
            <p>{incident.description}</p>
            <div className="detail-meta">
              <span><strong>Service</strong>{incident.service}</span>
              <span><strong>Severity</strong>{incident.severity}</span>
              <span><strong>Occurrences</strong>{incident.occurrence_count}</span>
              <span><strong>First seen</strong>{formatDate(incident.first_seen)}</span>
              <span><strong>SLA target</strong>{formatDate(incident.sla_due_at)}</span>
            </div>
          </section>
          <div className="two-column">
            <section className="panel">
              <div className="panel-header"><div><h2>Activity timeline</h2><p>Audited incident lifecycle changes</p></div><button className="icon-button" onClick={load} aria-label="Refresh activity"><RefreshCw size={16} /></button></div>
              {activity.length === 0 ? <div className="empty-state">No activity recorded.</div> : <div className="timeline">{activity.map((item) => <div key={item.id} className="timeline-item"><span className="timeline-dot" /><div><div className="timeline-heading"><strong>{item.action.replace("_", " ")}</strong><time>{formatDate(item.created_at)}</time></div><p>{item.message}</p><small>by {item.actor}</small></div></div>)}</div>}
            </section>
            <section className="panel">
              <div className="panel-header"><div><h2>Incident intelligence</h2><p>Evidence-based hypotheses from recent events</p></div><BrainCircuit size={19} className="panel-icon" /></div>
              {!analysis ? <div className="analysis-intro"><p>Analyze recent event patterns for this service. OpsPilot reports correlation and anomaly signals, not a confirmed root cause.</p><button className="button button-primary" disabled={busy} onClick={runAnalysis}><BrainCircuit size={15} /> Run analysis</button></div> : <>
                <p className="analysis-summary">{analysis.summary}</p>
                <div className={analysis.anomaly.detected ? "anomaly-banner warning" : "anomaly-banner"}>
                  <strong>{analysis.anomaly.detected ? "Elevated event rate detected" : "No event-rate anomaly detected"}</strong>
                  <span>{analysis.anomaly.current_window_events} events in latest {analysis.anomaly.window_minutes} minutes · baseline mean {analysis.anomaly.baseline_mean}</span>
                </div>
                {analysis.hypotheses.map((hypothesis, index) => <div className="hypothesis" key={hypothesis.type + index}>
                  <div><strong>{hypothesis.title}</strong><span className="confidence">{hypothesis.confidence} confidence</span></div>
                  <ul>{hypothesis.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
                  <p className="muted-cell">{hypothesis.caveat}</p>
                </div>)}
                <div className="limitations"><strong>Limitations</strong>{analysis.limitations.map((item) => <p key={item}>{item}</p>)}</div>
              </>}
            </section>
          </div>
        </>
      )}
    </AppShell>
  );
}
