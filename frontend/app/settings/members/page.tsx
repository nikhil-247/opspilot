"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Users } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import type { UserProfile } from "@/lib/types";

type Member = { user_id: string; email: string; full_name: string; role: string };

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    const [profile, team] = await Promise.all([
      apiFetch<UserProfile>("/api/v1/auth/me"),
      apiFetch<Member[]>("/api/v1/auth/members"),
    ]);
    setCurrentUser(profile);
    setMembers(team);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load team"));
  }, []);

  async function updateRole(userId: string, role: string) {
    setError("");
    setNotice("");
    try {
      await apiFetch<Member>("/api/v1/auth/members/" + userId + "/role", {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      setNotice("Member role updated.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update role");
    }
  }

  return (
    <AppShell title="Team & access" description="Review workspace membership and adjust role permissions.">
      <section className="panel">
        <div className="panel-header"><div><h2>Workspace members</h2><p>Membership is scoped to your current organization.</p></div><Users size={18} className="panel-icon" /></div>
        {error && <div className="inline-error">{error}</div>}
        {notice && <div className="form-success">{notice}</div>}
        {members.length === 0 ? <div className="empty-state">No members were returned.</div> : <div className="table-scroll">
          <table className="data-table">
            <thead><tr><th>Member</th><th>Email</th><th>Role</th><th>Permissions</th></tr></thead>
            <tbody>{members.map((member) => <tr key={member.user_id}>
              <td><strong>{member.full_name}</strong></td><td>{member.email}</td>
              <td>{currentUser?.role === "owner" || currentUser?.role === "admin" ? (
                <select value={member.role} disabled={member.user_id === currentUser?.id} onChange={(event) => updateRole(member.user_id, event.target.value)}>
                  <option value="admin">Admin</option><option value="on_call">On-call</option><option value="viewer">Viewer</option><option value="owner" disabled>Owner</option>
                </select>
              ) : <span className="status status-acknowledged">{member.role.replace("_", " ")}</span>}</td>
              <td><span className="permission-hint"><ShieldCheck size={14} /> {member.role === "viewer" ? "Read only" : "Can update incidents"}</span></td>
            </tr>)}</tbody>
          </table>
        </div>}
      </section>
      <div className="info-strip"><ShieldCheck size={17} /><span>Viewer accounts can read workspace data. On-call, admin and owner roles can ingest events and change incident state. Only owners/admins can manage memberships; owner assignment is restricted.</span></div>
    </AppShell>
  );
}
