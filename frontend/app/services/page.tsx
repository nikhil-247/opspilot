"use client";

import { FormEvent, useEffect, useState } from "react";
import { Boxes, GitBranch, Plus } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch, formatDate } from "@/lib/api";

type Dependency = {
  id: string;
  source_service: string;
  target_service: string;
  relationship_type: string;
  created_at: string;
};

export default function ServicesPage() {
  const [items, setItems] = useState<Dependency[]>([]);
  const [source, setSource] = useState("checkout-api");
  const [target, setTarget] = useState("payment-service");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setItems(await apiFetch<Dependency[]>("/api/v1/services/dependencies"));
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load service map"));
  }, []);

  async function addDependency(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiFetch<Dependency>("/api/v1/services/dependencies", {
        method: "POST",
        body: JSON.stringify({
          source_service: source,
          target_service: target,
          relationship_type: "depends_on",
        }),
      });
      setNotice("Dependency saved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save dependency");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Service map" description="Record and inspect service-to-service dependencies for your organization.">
      <div className="two-column">
        <section className="panel">
          <div className="panel-header"><div><h2>Add dependency</h2><p>Describe which service relies on another</p></div><Plus size={18} className="panel-icon" /></div>
          <form onSubmit={addDependency} className="form-stack">
            <label>Source service<input value={source} onChange={(event) => setSource(event.target.value)} required maxLength={100} /></label>
            <label>Depends on<input value={target} onChange={(event) => setTarget(event.target.value)} required maxLength={100} /></label>
            {notice && <div className="form-success">{notice}</div>}
            {error && <div className="form-error">{error}</div>}
            <button className="button button-primary" disabled={busy}><Plus size={15} /> Save dependency</button>
          </form>
        </section>
        <section className="panel">
          <div className="panel-header"><div><h2>Dependency edges</h2><p>{items.length} relationships stored</p></div><GitBranch size={18} className="panel-icon" /></div>
          {items.length === 0 ? <div className="empty-state"><Boxes size={25} />No service relationships have been added.</div> : <div className="dependency-list">{items.map((item) => <div className="dependency-row" key={item.id}>
            <div><strong>{item.source_service}</strong><small>{item.relationship_type.replace("_", " ")}</small></div>
            <GitBranch size={18} />
            <div><strong>{item.target_service}</strong><small>Recorded {formatDate(item.created_at)}</small></div>
          </div>)}</div>}
        </section>
      </div>
      <div className="info-strip"><GitBranch size={17} /><span>This is a tenant-scoped dependency registry. Automatic discovery from traces and a visual topology graph are subsequent enhancements.</span></div>
    </AppShell>
  );
}
