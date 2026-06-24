import { AlertTriangle, Clock, Gauge, X } from "lucide-react";
import type { TrackAnalysis } from "../lib/types";
import { formatDuration } from "../lib/format";
import { Waveform } from "./Waveform";

export function TrackDetail({ analysis, onClose }: { analysis: TrackAnalysis; onClose: () => void }) {
  return (
    <div className="detail-backdrop" onClick={onClose}>
      <aside className="detail-drawer" onClick={(event) => event.stopPropagation()}>
        <button className="icon-button close" onClick={onClose}><X /></button>
        <p className="eyebrow">Track intelligence</p>
        <h2>{analysis.title}</h2>
        <p className="muted">{analysis.artist || "Unknown artist"}</p>
        <div className="detail-metrics">
          <div><Gauge /><strong>{Math.round(analysis.estimated_bpm)}</strong><span>BPM</span></div>
          <div><Clock /><strong>{formatDuration(analysis.duration)}</strong><span>Length</span></div>
          <div><strong>{Math.round(analysis.analysis_confidence * 100)}%</strong><span>Confidence</span></div>
        </div>
        <Waveform values={analysis.energy_curve} />
        <h3>Hot cues</h3>
        <div className="cue-list">
          {analysis.hot_cues.map((cue) => (
            <div className="cue-row" key={cue.label}>
              <span>{cue.label.replace("Hot Cue ", "")}</span>
              <div><strong>{cue.name}</strong><small>{cue.reason}</small></div>
              <time>{formatDuration(cue.timestamp)}</time>
            </div>
          ))}
        </div>
        <h3>Loop suggestion</h3>
        <div className="note-card"><strong>{analysis.loop_cue.bars} bars · {formatDuration(analysis.loop_cue.start)}</strong><p>{analysis.loop_cue.reason}</p></div>
        {analysis.warnings.length > 0 && <div className="warning-card"><AlertTriangle /><div><strong>Verify before performing</strong>{analysis.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div></div>}
      </aside>
    </div>
  );
}
