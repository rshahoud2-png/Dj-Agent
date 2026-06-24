import { Download, Headphones, MoveRight } from "lucide-react";
import type { DjExportTarget, Setlist } from "../lib/types";
import { formatDuration } from "../lib/format";

export function PerformanceView({
  setlist,
  onExport,
  onDjExport,
}: {
  setlist: Setlist | null;
  onExport: (format: "csv" | "json") => void;
  onDjExport: (target: DjExportTarget) => void;
}) {
  if (!setlist) {
    return <section><div className="page-heading"><div><p className="eyebrow">Rehearsal mode</p><h1>Performance View</h1></div></div><div className="panel empty-state"><Headphones size={36} /><h2>No set loaded</h2><p>Generate a set in Event Set Builder to see song order, cues, and transition instructions here.</p></div></section>;
  }
  return (
    <section>
      <div className="page-heading">
        <div><p className="eyebrow">{setlist.event_type}</p><h1>{setlist.name}</h1><p>{setlist.items.length} tracks · {Math.round(setlist.confidence_score * 100)}% confidence</p></div>
        <div className="heading-actions export-actions">
          <button className="button secondary" onClick={() => onExport("csv")}><Download size={17} /> CSV</button>
          <button className="button secondary" onClick={() => onExport("json")}><Download size={17} /> JSON</button>
          <button className="button secondary" onClick={() => onDjExport("rekordbox")}>rekordbox</button>
          <button className="button secondary" onClick={() => onDjExport("virtualdj")}>VirtualDJ</button>
          <button className="button primary" onClick={() => onDjExport("serato")}>Serato bridge</button>
        </div>
      </div>
      <div className="performance-list">
        {setlist.items.map((item) => (
          <article className="performance-card" key={`${item.position}-${item.track.track_id}`}>
            <div className="position">{String(item.position).padStart(2, "0")}</div>
            <div className="performance-main">
              <span className="section-tag">{item.section}</span>
              <h2>{item.track.title}</h2><p>{item.track.artist || "Unknown artist"} · {Math.round(item.track.estimated_bpm)} BPM · {formatDuration(item.track.duration)}</p>
              <div className="cue-chips">{item.track.hot_cues.map((cue) => <span key={cue.label}><b>{cue.label.replace("Hot Cue ", "")}</b>{cue.name} {formatDuration(cue.timestamp)}</span>)}</div>
              {item.transition && <div className="transition-instruction"><MoveRight /><div><strong>{item.transition.recommended_transition_type} · {item.transition.suggested_transition_length_bars} bars</strong><p>{item.transition.dj_performance_instruction}</p></div><span className="compatibility">{item.transition.compatibility_score}%</span></div>}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
