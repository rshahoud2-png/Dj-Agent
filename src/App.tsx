import { useCallback, useEffect, useState } from "react";
import { open, save } from "@tauri-apps/plugin-dialog";
import { engineApi } from "./lib/api";
import type { DjExportTarget, EventType, Setlist, Track, TrackAnalysis } from "./lib/types";
import { Sidebar, type View } from "./components/Sidebar";
import { LibraryView } from "./components/LibraryView";
import { QueueView } from "./components/QueueView";
import { SetBuilderView } from "./components/SetBuilderView";
import { PerformanceView } from "./components/PerformanceView";
import { SettingsView } from "./components/SettingsView";
import { TrackDetail } from "./components/TrackDetail";

function App() {
  const [view, setView] = useState<View>("library");
  const [tracks, setTracks] = useState<Track[]>([]);
  const [folder, setFolder] = useState(localStorage.getItem("dj-agent-folder") ?? "");
  const [databasePath, setDatabasePath] = useState("");
  const [engineReady, setEngineReady] = useState(false);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [activeTrackId, setActiveTrackId] = useState<number | null>(null);
  const [processed, setProcessed] = useState(0);
  const [queueTotal, setQueueTotal] = useState(0);
  const [selectedAnalysis, setSelectedAnalysis] = useState<TrackAnalysis | null>(null);
  const [eventType, setEventType] = useState<EventType>("Arabic Wedding");
  const [duration, setDuration] = useState(240);
  const [setName, setSetName] = useState("Saturday Night Set");
  const [setlist, setSetlist] = useState<Setlist | null>(null);
  const [toast, setToast] = useState("");

  const notify = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3500);
  }, []);

  const refreshTracks = useCallback(async () => {
    const result = await engineApi.listTracks();
    setTracks(result);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const connect = async () => {
      for (let attempt = 0; attempt < 25 && !cancelled; attempt += 1) {
        try {
          const health = await engineApi.health();
          if (!cancelled) {
            setEngineReady(true);
            setDatabasePath(health.database_path);
            await refreshTracks();
          }
          return;
        } catch {
          await new Promise((resolve) => window.setTimeout(resolve, 400));
        }
      }
      if (!cancelled) notify("The local analysis engine did not start. See README troubleshooting.");
    };
    void connect();
    return () => { cancelled = true; };
  }, [notify, refreshTracks]);

  const chooseFolder = async () => {
    const selected = await open({ directory: true, multiple: false, title: "Select your music library" });
    if (!selected || Array.isArray(selected)) return;
    setBusy(true);
    try {
      const result = await engineApi.scanLibrary(selected);
      setFolder(selected);
      localStorage.setItem("dj-agent-folder", selected);
      await refreshTracks();
      notify(`Found ${result.discovered} audio files · ${result.added} new tracks`);
    } catch (error) {
      notify(error instanceof Error ? error.message : "Folder scan failed");
    } finally {
      setBusy(false);
    }
  };

  const analyzePending = async () => {
    const queue = tracks.filter((track) => track.status === "pending" || track.status === "failed");
    if (!queue.length) return;
    setBusy(true);
    setView("queue");
    setProcessed(0);
    setQueueTotal(queue.length);
    for (const [index, track] of queue.entries()) {
      setActiveTrackId(track.id);
      setTracks((current) => current.map((item) => item.id === track.id ? { ...item, status: "analyzing" } : item));
      try {
        await engineApi.analyzeTrack(track.id);
      } catch (error) {
        notify(`${track.title}: ${error instanceof Error ? error.message : "analysis failed"}`);
      }
      setProcessed(index + 1);
      await refreshTracks();
    }
    setActiveTrackId(null);
    setBusy(false);
    notify("Local library analysis complete");
  };

  const selectTrack = async (track: Track) => {
    if (track.status !== "complete") return notify("Analyze this track before opening cue details.");
    try {
      setSelectedAnalysis(await engineApi.getAnalysis(track.id));
    } catch (error) {
      notify(error instanceof Error ? error.message : "Could not load analysis");
    }
  };

  const generateSet = async () => {
    setBusy(true);
    try {
      const generated = await engineApi.generateSetlist(eventType, duration, setName);
      setSetlist(generated);
      setView("performance");
      notify("Setlist generated locally");
    } catch (error) {
      notify(error instanceof Error ? error.message : "Setlist generation failed");
    } finally {
      setBusy(false);
    }
  };

  const exportSet = async (format: "csv" | "json") => {
    if (!setlist) return;
    const destination = await save({
      title: `Export ${setlist.name}`,
      defaultPath: `${setlist.name.replace(/[^\w-]+/g, "-")}.${format}`,
      filters: [{ name: format.toUpperCase(), extensions: [format] }],
    });
    if (!destination) return;
    try {
      const result = await engineApi.exportSetlist(setlist.id, format, destination);
      notify(`Exported to ${result.path}`);
    } catch (error) {
      notify(error instanceof Error ? error.message : "Export failed");
    }
  };

  const exportDjSoftware = async (target: DjExportTarget) => {
    if (!setlist) return;
    const extensions: Record<DjExportTarget, string> = {
      rekordbox: "xml",
      virtualdj: "xml",
      serato: "m3u8",
    };
    const extension = extensions[target];
    const destination = await save({
      title: `Export ${setlist.name} for ${target}`,
      defaultPath: `${setlist.name.replace(/[^\w-]+/g, "-")}-${target}.${extension}`,
      filters: [{ name: target, extensions: [extension] }],
    });
    if (!destination) return;
    try {
      const result = await engineApi.exportDjSoftware(setlist.id, target, destination);
      notify(`Exported ${result.paths.length} ${target} file${result.paths.length === 1 ? "" : "s"}`);
    } catch (error) {
      notify(error instanceof Error ? error.message : `${target} export failed`);
    }
  };

  let content;
  if (view === "queue") {
    content = <QueueView tracks={tracks} activeTrackId={activeTrackId} processed={processed} total={queueTotal} />;
  } else if (view === "builder") {
    content = <SetBuilderView tracks={tracks} eventType={eventType} duration={duration} name={setName} setlist={setlist} busy={busy} onEventType={setEventType} onDuration={setDuration} onName={setSetName} onGenerate={generateSet} />;
  } else if (view === "performance") {
    content = <PerformanceView setlist={setlist} onExport={exportSet} onDjExport={exportDjSoftware} />;
  } else if (view === "settings") {
    content = <SettingsView databasePath={databasePath} folder={folder} />;
  } else {
    content = <LibraryView tracks={tracks} folder={folder} search={search} busy={busy} onSearch={setSearch} onChooseFolder={chooseFolder} onAnalyzePending={analyzePending} onSelectTrack={selectTrack} />;
  }

  return (
    <div className="app-shell">
      <Sidebar active={view} onChange={setView} engineReady={engineReady} />
      <main className="content">{content}</main>
      {selectedAnalysis && <TrackDetail analysis={selectedAnalysis} onClose={() => setSelectedAnalysis(null)} />}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

export default App;
