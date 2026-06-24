import { AlertTriangle, CheckCircle2, LoaderCircle, Music2 } from "lucide-react";
import type { Track } from "../lib/types";

export function QueueView({
  tracks,
  activeTrackId,
  processed,
  total,
}: {
  tracks: Track[];
  activeTrackId: number | null;
  processed: number;
  total: number;
}) {
  const queue = tracks.filter((track) => ["pending", "analyzing", "failed"].includes(track.status));
  const progress = total ? Math.round((processed / total) * 100) : 0;
  return (
    <section>
      <div className="page-heading">
        <div><p className="eyebrow">Sequential processing</p><h1>Analysis Queue</h1><p>One track at a time keeps memory use predictable, even with large libraries.</p></div>
      </div>
      <div className="panel queue-summary">
        <div className="queue-progress-row">
          <div><strong>{activeTrackId ? "Analyzing your library" : "Queue ready"}</strong><span>{processed} of {total || queue.length} tracks processed</span></div>
          <strong className="gold-text">{progress}%</strong>
        </div>
        <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
      </div>
      <div className="panel queue-list">
        {queue.length === 0 ? <div className="empty-state compact"><CheckCircle2 size={32} /><h2>Queue is clear</h2><p>Every discovered track has been analyzed.</p></div> :
          queue.map((track) => (
            <div className="queue-item" key={track.id}>
              <div className="queue-icon">
                {activeTrackId === track.id ? <LoaderCircle className="spin" /> : track.status === "failed" ? <AlertTriangle /> : <Music2 />}
              </div>
              <div><strong>{track.title}</strong><span>{track.path}</span>{track.error && <small>{track.error}</small>}</div>
              <span className={`status-badge ${activeTrackId === track.id ? "analyzing" : track.status}`}>{activeTrackId === track.id ? "analyzing" : track.status}</span>
            </div>
          ))}
      </div>
    </section>
  );
}
