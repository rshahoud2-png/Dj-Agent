import {
  AudioLines,
  Disc3,
  Library,
  ListMusic,
  Radio,
  Settings,
} from "lucide-react";

export type View = "library" | "queue" | "builder" | "performance" | "settings";

const items: { id: View; label: string; icon: typeof Library }[] = [
  { id: "library", label: "Music Library", icon: Library },
  { id: "queue", label: "Analysis Queue", icon: AudioLines },
  { id: "builder", label: "Event Set Builder", icon: ListMusic },
  { id: "performance", label: "Performance View", icon: Radio },
  { id: "settings", label: "Local Settings", icon: Settings },
];

export function Sidebar({
  active,
  onChange,
  engineReady,
}: {
  active: View;
  onChange: (view: View) => void;
  engineReady: boolean;
}) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Disc3 size={26} /></div>
        <div>
          <strong>DJ Agent</strong>
          <span>Desktop</span>
        </div>
      </div>
      <nav className="nav-list" aria-label="Primary navigation">
        {items.map(({ id, label, icon: Icon }) => (
          <button
            className={active === id ? "nav-item active" : "nav-item"}
            key={id}
            onClick={() => onChange(id)}
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="engine-state">
        <span className={engineReady ? "status-dot ready" : "status-dot"} />
        <div>
          <strong>{engineReady ? "Local engine online" : "Starting engine"}</strong>
          <span>127.0.0.1 · private</span>
        </div>
      </div>
    </aside>
  );
}
