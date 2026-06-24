import { Database, HardDrive, ShieldCheck } from "lucide-react";

export function SettingsView({ databasePath, folder }: { databasePath: string; folder: string }) {
  return (
    <section>
      <div className="page-heading"><div><p className="eyebrow">Private by design</p><h1>Local Settings</h1><p>Core analysis and planning stay on this Windows PC.</p></div></div>
      <div className="settings-grid">
        <div className="panel setting-card"><ShieldCheck /><div><strong>Offline core</strong><p>No Fly.io, Vercel, cloud backend, account, or audio upload is required.</p></div></div>
        <div className="panel setting-card"><Database /><div><strong>SQLite database</strong><p>{databasePath || "Waiting for local engine…"}</p></div></div>
        <div className="panel setting-card"><HardDrive /><div><strong>Music folder</strong><p>{folder || "No folder selected"}</p></div></div>
      </div>
      <div className="panel roadmap-card"><p className="eyebrow">Prepared integrations</p><h2>Export roadmap</h2><div className="integration-grid"><span>rekordbox XML</span><span>VirtualDJ database.xml</span><span>Serato crates & cues</span><span>Optional encrypted cloud sync</span></div></div>
    </section>
  );
}
