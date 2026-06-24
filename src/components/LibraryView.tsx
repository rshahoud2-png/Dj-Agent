import { FolderOpen, Play, RefreshCw, Search } from "lucide-react";
import type { Track } from "../lib/types";
import { confidenceLabel, formatBytes, formatDuration } from "../lib/format";

export function LibraryView({
  tracks,
  folder,
  search,
  busy,
  onSearch,
  onChooseFolder,
  onAnalyzePending,
  onSelectTrack,
}: {
  tracks: Track[];
  folder: string;
  search: string;
  busy: boolean;
  onSearch: (value: string) => void;
  onChooseFolder: () => void;
  onAnalyzePending: () => void;
  onSelectTrack: (track: Track) => void;
}) {
  const filtered = tracks.filter((track) =>
    `${track.title} ${track.artist} ${track.filename}`.toLowerCase().includes(search.toLowerCase()),
  );
  const pending = tracks.filter((track) => track.status === "pending" || track.status === "failed").length;

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your local collection</p>
          <h1>Music Library</h1>
          <p>Scan and analyze tracks without sending a single audio file to the cloud.</p>
        </div>
        <div className="heading-actions">
          <button className="button secondary" onClick={onChooseFolder} disabled={busy}>
            <FolderOpen size={17} /> Select music folder
          </button>
          <button className="button primary" onClick={onAnalyzePending} disabled={busy || pending === 0}>
            {busy ? <RefreshCw className="spin" size={17} /> : <Play size={17} />}
            Analyze {pending || ""} tracks
          </button>
        </div>
      </div>

      <div className="stat-grid">
        <Stat label="Library tracks" value={String(tracks.length)} />
        <Stat label="Analyzed" value={String(tracks.filter((track) => track.status === "complete").length)} />
        <Stat label="Waiting" value={String(pending)} />
        <Stat label="Storage" value={formatBytes(tracks.reduce((sum, track) => sum + track.file_size, 0))} />
      </div>

      <div className="panel">
        <div className="panel-toolbar">
          <div>
            <strong>{folder ? "Selected folder" : "No music folder selected"}</strong>
            <span className="path-label">{folder || "Choose a folder to begin scanning."}</span>
          </div>
          <label className="search">
            <Search size={16} />
            <input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="Search tracks" />
          </label>
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"><FolderOpen size={30} /></div>
            <h2>Your decks are waiting</h2>
            <p>Select a folder containing MP3, WAV, FLAC, AIFF, M4A, AAC, or OGG files.</p>
            <button className="button primary" onClick={onChooseFolder}>Choose music folder</button>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Track</th><th>BPM</th><th>Length</th><th>Format</th><th>Analysis</th></tr>
              </thead>
              <tbody>
                {filtered.map((track) => (
                  <tr key={track.id}>
                    <td>
                      <button className="track-open" onClick={() => onSelectTrack(track)}>
                        <span className="track-title"><strong>{track.title || track.filename}</strong><span>{track.artist || track.album || track.path}</span></span>
                      </button>
                    </td>
                    <td>{track.bpm ? Math.round(track.bpm) : "—"}</td>
                    <td>{formatDuration(track.duration)}</td>
                    <td><span className="format-pill">{track.extension.replace(".", "").toUpperCase()}</span></td>
                    <td><StatusBadge status={track.status} label={confidenceLabel(track.analysis_confidence)} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="stat-card"><span>{label}</span><strong>{value}</strong></div>;
}

function StatusBadge({ status, label }: { status: Track["status"]; label: string }) {
  return <span className={`status-badge ${status}`}>{status === "complete" ? label : status}</span>;
}
