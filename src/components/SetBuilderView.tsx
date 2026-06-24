import { CalendarDays, Sparkles } from "lucide-react";
import type { EventType, Setlist, Track } from "../lib/types";

const events: EventType[] = ["Arabic Wedding", "Wedding", "Club", "Lounge", "Bar", "Corporate", "Cafe"];

export function SetBuilderView({
  tracks,
  eventType,
  duration,
  name,
  setlist,
  busy,
  onEventType,
  onDuration,
  onName,
  onGenerate,
}: {
  tracks: Track[];
  eventType: EventType;
  duration: number;
  name: string;
  setlist: Setlist | null;
  busy: boolean;
  onEventType: (event: EventType) => void;
  onDuration: (duration: number) => void;
  onName: (name: string) => void;
  onGenerate: () => void;
}) {
  const ready = tracks.filter((track) => track.status === "complete").length;
  return (
    <section>
      <div className="page-heading">
        <div><p className="eyebrow">Event intelligence</p><h1>Event Set Builder</h1><p>Shape an event-ready flow from analyzed tracks and transparent DJ rules.</p></div>
      </div>
      <div className="builder-grid">
        <div className="panel builder-form">
          <div className="section-icon"><CalendarDays /></div>
          <h2>Plan the room</h2>
          <label><span>Setlist name</span><input value={name} onChange={(event) => onName(event.target.value)} /></label>
          <label><span>Event template</span><select value={eventType} onChange={(event) => onEventType(event.target.value as EventType)}>{events.map((event) => <option key={event}>{event}</option>)}</select></label>
          <label><span>Event duration</span><select value={duration} onChange={(event) => onDuration(Number(event.target.value))}>{[60, 90, 120, 180, 240, 300].map((minutes) => <option value={minutes} key={minutes}>{minutes / 60} hour{minutes > 60 ? "s" : ""}</option>)}</select></label>
          <div className="library-readiness"><strong>{ready} analyzed tracks</strong><span>{ready ? "Ready for set generation" : "Analyze music before building a set"}</span></div>
          <button className="button primary wide" onClick={onGenerate} disabled={busy || ready === 0}><Sparkles size={17} />{busy ? "Building set…" : "Generate DJ-ready set"}</button>
        </div>
        <div className="panel template-preview">
          <p className="eyebrow">{eventType}</p>
          <h2>Suggested event arc</h2>
          <EventArc event={eventType} />
          {setlist && <div className="generated-callout"><strong>{setlist.items.length} tracks arranged</strong><span>{Math.round(setlist.confidence_score * 100)}% set confidence · Open Performance View to rehearse.</span></div>}
        </div>
      </div>
    </section>
  );
}

function EventArc({ event }: { event: EventType }) {
  const sections: Record<EventType, string[]> = {
    "Arabic Wedding": ["Dinner", "Entrance", "Arabic Warmup", "Dabke", "Arabic Peak", "English / Latin Peak", "Slow Dance", "Closing"],
    Wedding: ["Dinner", "Entrance", "First Dance", "Open Dance", "Throwbacks", "Peak Party", "Closing"],
    Club: ["Warmup", "Build Up", "Peak", "Reset", "Peak 2", "Closing"],
    Lounge: ["Background", "Warm Groove", "Social Energy", "Cooldown"],
    Bar: ["Background", "Warm Groove", "Social Energy", "Late Energy", "Cooldown"],
    Corporate: ["Arrival", "Networking", "Dinner", "Feature", "Social", "Closing"],
    Cafe: ["Background", "Warm Groove", "Social Energy", "Cooldown"],
  };
  return <div className="event-arc">{sections[event].map((section, index) => <div key={section}><span>{String(index + 1).padStart(2, "0")}</span><strong>{section}</strong></div>)}</div>;
}
