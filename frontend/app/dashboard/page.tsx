"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Activity, ArrowUpRight, Clock3, ShieldAlert, Siren, Workflow } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch, formatDate } from "@/lib/api";
import type { Incident, IncidentList } from "@/lib/types";

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("active");
  const [priority, setPriority] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function refreshIncidents(showLoading: boolean) {
      if (showLoading) setLoading(true);
      const params = new URLSearchParams({ limit: "100" });
      if (status === "active") params.set("status", "open");
      if (status === "acknowledged") params.set("status", "acknowledged");
      if (status === "resolved") params.set("status", "resolved");
      if (priority !== "all") params.set("priority", priority);
      try {
        const data = await apiFetch<IncidentList>("/api/v1/incidents?" + params.toString());
        if (!active) return;
        setIncidents(data.items);
        setTotal(data.total);
        setError("");
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unable to load incidents");
      } finally {
        if (active && showLoading) setLoading(false);
      }
    }

    void refreshIncidents(true);
    const refreshTimer = window.setInterval(() => {
      void refreshIncidents(false);
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(refreshTimer);
    };
  }, [status, priority]);

  const stats = useMemo(() => ({
    active: incidents.filter((item) => item.status !== "resolved").length,
    critical: incidents.filter((item) => item.priority === "P1" && item.status !== "resolved").length,
    acknowledged: incidents.filter((item) => item.status === "acknowledged").length,
    resolved: incidents.filter((item) => item.status === "resolved").length,
  }), [incidents]);

  return (
    <AppShell title="Incident overview" description="A live view of service health, response activity and open operational work.">
      <div className="stats-grid">
        <StatCard label="Open incidents" value={stats.active} icon={<ShieldAlert size={19} />} tone="blue" detail="Current result set" />
        <StatCard label="P1 critical" value={stats.critical} icon={<Siren size={19} />} tone="red" detail="Needs immediate attention" />
        <StatCard label="Acknowledged" value={stats.acknowledged} icon={<Clock3 size={19} />} tone="amber" detail="Being investigated" />
        <StatCard label="Resolved" value={stats.resolved} icon={<Activity size={19} />} tone="green" detail="In current result set" />
      </div>
      <section className="panel">
        <div className="panel-header">
          <div><h2>Incident queue</h2><p>{total} matching incident{total === 1 ? "" : "s"} in this workspace</p></div>
          <div className="filter-row">
            <select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter by status">
              <option value="active">Open</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="all">All statuses</option>
            </select>
            <select value={priority} onChange={(event) => setPriority(event.target.value)} aria-label="Filter by priority">
              <option value="all">All priorities</option><option value="P1">P1</option><option value="P2">P2</option><option value="P3">P3</option>
            </select>
          </div>
        </div>
        {error && <div className="inline-error">{error}</div>}
        {loading ? <div className="empty-state">Loading incidents from the API…</div> : incidents.length === 0 ? (
          <div className="empty-state"><Workflow size={27} /><strong>No incidents found</strong><span>Try another filter or send a test event from Event explorer.</span><Link href="/events" className="text-link">Open event explorer <ArrowUpRight size={14} /></Link></div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th>Incident</th><th>Service</th><th>Priority</th><th>Status</th><th>Occurrences</th><th>Last seen</th><th /></tr></thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td><Link href={"/incidents/" + incident.id} className="incident-link"><strong>{incident.title}</strong><small>{incident.id.slice(0, 8)}</small></Link></td>
                    <td><span className="service-name">{incident.service}</span></td>
                    <td><span className={"priority priority-" + incident.priority.toLowerCase()}>{incident.priority}</span></td>
                    <td><span className={"status status-" + incident.status}>{incident.status}</span></td>
                    <td>{incident.occurrence_count}</td>
                    <td className="muted-cell">{formatDate(incident.last_seen)}</td>
                    <td><Link href={"/incidents/" + incident.id} className="icon-link"><ArrowUpRight size={16} /></Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="panel-footnote">Showing up to 100 records. Counts on this page are calculated from the returned API results.</div>
      </section>
      <section className="info-strip"><Activity size={17} /><span>Incident data is loaded from your authenticated organization. No sample cards or synthetic incident counts are displayed.</span></section>
    </AppShell>
  );
}

function StatCard({ label, value, icon, tone, detail }: {
  label: string; value: number; icon: React.ReactNode; tone: string; detail: string;
}) {
  return <div className="stat-card"><div className={"stat-icon " + tone}>{icon}</div><div className="stat-copy"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></div>;
}
