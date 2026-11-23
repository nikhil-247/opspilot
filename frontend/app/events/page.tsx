"use client";

import { FormEvent, useEffect, useState } from "react";
import { Activity, Plus, Send } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch, formatDate } from "@/lib/api";
import type { EventRecord } from "@/lib/types";

export default function EventsPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [service, setService] = useState("payment-service");
  const [eventType, setEventType] = useState("database_connection_error");
  const [severity, setSeverity] = useState("error");
  const [serviceFilter, setServiceFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("Database connection pool exhausted");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    const params = new URLSearchParams({ limit: "100" });
    if (serviceFilter.trim()) params.set("service", serviceFilter.trim());
    if (severityFilter !== "all") params.set("severity", severityFilter);
    if (search.trim()) params.set("search", search.trim());
    setEvents(await apiFetch<EventRecord[]>("/api/v1/events?" + params.toString()));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load events"));
  }, [serviceFilter, severityFilter, search]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await apiFetch<{
        event: EventRecord; incident: { id: string } | null; incident_created: boolean;
      }>("/api/v1/events", {
        method: "POST",
        body: JSON.stringify({
          source: "opspilot-console",
          service,
          event_type: eventType,
          severity,
          message,
          attributes: { environment: "demo", created_from: "web-console" },
        }),
      });
      setNotice(result.incident_created
        ? "Event stored and a new incident was created."
        : result.incident
          ? "Event stored and attached to an existing incident."
          : "Informational event stored without creating an incident.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to submit event");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Event explorer" description="Inspect events stored by the API and send test events into the incident pipeline.">
      <div className="two-column events-layout">
        <section className="panel">
          <div className="panel-header"><div><h2>Send a test event</h2><p>Writes to the authenticated workspace database</p></div><Plus size={18} className="panel-icon" /></div>
          <form onSubmit={submit} className="form-stack">
            <label>Service<input value={service} onChange={(event) => setService(event.target.value)} required maxLength={100} /></label>
            <label>Event type<input value={eventType} onChange={(event) => setEventType(event.target.value)} required maxLength={100} /></label>
            <label>Severity<select value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="info">Info</option><option value="warning">Warning</option><option value="error">Error</option><option value="critical">Critical</option></select></label>
            <label>Message<textarea rows={4} value={message} onChange={(event) => setMessage(event.target.value)} required maxLength={5000} /></label>
            {notice && <div className="form-success">{notice}</div>}
            {error && <div className="form-error">{error}</div>}
            <button className="button button-primary button-wide" disabled={busy}><Send size={15} /> {busy ? "Sending event…" : "Ingest event"}</button>
          </form>
        </section>
        <section className="panel">
          <div className="panel-header"><div><h2>Recent events</h2><p>{events.length} records returned by the API</p></div><Activity size={18} className="panel-icon" /></div>
          {events.length === 0 ? <div className="empty-state">No events yet. Send your first test event.</div> : <div className="event-list">{events.map((item) => <div className="event-item" key={item.id}>
            <div className="event-item-top"><span className={"severity severity-" + item.severity}>{item.severity}</span><time>{formatDate(item.received_at)}</time></div>
            <strong>{item.event_type}</strong><p>{item.message}</p>
            <div className="event-item-meta"><span>{item.service}</span><span>{item.incident_id ? "Linked to incident " + item.incident_id.slice(0, 8) : "No incident"}</span></div>
          </div>)}</div>}
        </section>
      </div>
    </AppShell>
  );
}
