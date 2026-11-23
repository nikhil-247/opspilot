"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity, Boxes, ChartNoAxesCombined, CircleAlert, LogOut,
  RadioTower, Settings, ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import type { UserProfile } from "@/lib/types";

const navigation = [
  { href: "/dashboard", label: "Overview", icon: ChartNoAxesCombined },
  { href: "/events", label: "Event explorer", icon: RadioTower },
  { href: "/services", label: "Service map", icon: Boxes },
  { href: "/settings/members", label: "Team & access", icon: ShieldCheck },
];

export function AppShell({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title: string;
  description?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    apiFetch<UserProfile>("/api/v1/auth/me")
      .then((profile) => {
        if (active) setUser(profile);
      })
      .catch(() => {
        if (active) router.replace("/login");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [router]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  if (loading || !user) {
    return (
      <main className="auth-loading">
        <div className="loading-mark"><Activity size={23} /></div>
        <span>Loading your workspace</span>
      </main>
    );
  }

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Link href="/dashboard" className="brand">
          <span className="brand-icon"><Activity size={21} /></span>
          <span>OpsPilot<small>INCIDENT OPERATIONS</small></span>
        </Link>
        <div className="workspace-chip">
          <span className="workspace-dot" />
          <span><strong>{user.organization_name}</strong><small>{user.role.replace("_", " ")}</small></span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link key={item.href} href={item.href} className={active ? "nav-link active" : "nav-link"}>
                <Icon size={17} strokeWidth={1.8} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="user-chip">
            <div className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</div>
            <span><strong>{user.full_name}</strong><small>{user.email}</small></span>
          </div>
          <button className="logout-button" onClick={logout}><LogOut size={16} /> Sign out</button>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="eyebrow"><CircleAlert size={13} /> OPERATIONS CENTER</div>
            <h1>{title}</h1>
            {description && <p>{description}</p>}
          </div>
          <div className="topbar-status"><span className="pulse-dot" /> API session active</div>
        </header>
        <div className="page-content">{children}</div>
        <footer className="app-footer">
          <span>OpsPilot · Engineering preview</span>
          <span><Settings size={13} /> Authenticated workspace · tenant scoped</span>
        </footer>
      </main>
    </div>
  );
}
