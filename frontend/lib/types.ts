export type UserProfile = {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: "owner" | "admin" | "on_call" | "viewer" | string;
};

export type Incident = {
  id: string;
  title: string;
  description: string;
  service: string;
  severity: string;
  priority: "P1" | "P2" | "P3";
  status: "open" | "acknowledged" | "resolved";
  occurrence_count: number;
  first_seen: string;
  last_seen: string;
  sla_due_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type IncidentList = {
  items: Incident[];
  total: number;
  limit: number;
  offset: number;
};

export type EventRecord = {
  id: string;
  source: string;
  service: string;
  event_type: string;
  severity: string;
  message: string;
  attributes: Record<string, unknown>;
  occurred_at: string;
  received_at: string;
  incident_id: string | null;
};

export type Activity = {
  id: string;
  incident_id: string;
  action: string;
  actor: string;
  message: string;
  created_at: string;
};
