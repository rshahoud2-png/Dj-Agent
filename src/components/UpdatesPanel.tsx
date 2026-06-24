import { getVersion } from "@tauri-apps/api/app";
import { relaunch } from "@tauri-apps/plugin-process";
import { check, type Update } from "@tauri-apps/plugin-updater";
import { Download, RefreshCw, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type UpdateState = "idle" | "checking" | "current" | "available" | "downloading" | "restarting" | "error";

export function UpdatesPanel() {
  const [currentVersion, setCurrentVersion] = useState("0.2.0");
  const [state, setState] = useState<UpdateState>("idle");
  const [availableVersion, setAvailableVersion] = useState("");
  const [releaseDate, setReleaseDate] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("Updates are downloaded from signed GitHub Releases.");
  const updateRef = useRef<Update | null>(null);

  useEffect(() => {
    getVersion().then(setCurrentVersion).catch(() => {
      setMessage("Version details are available in the installed desktop app.");
    });
  }, []);

  async function checkForUpdates() {
    setState("checking");
    setMessage("Checking GitHub Releases...");
    updateRef.current = null;
    try {
      const update = await check({ timeout: 15_000 });
      if (!update) {
        setState("current");
        setMessage("You are running the latest version.");
        return;
      }
      updateRef.current = update;
      setAvailableVersion(update.version);
      setReleaseDate(update.date ?? "");
      setReleaseNotes(update.body?.trim() || "This release does not include release notes.");
      setState("available");
      setMessage(`DJ Agent Desktop ${update.version} is ready to install.`);
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Could not check for updates.");
    }
  }

  async function installUpdate() {
    const update = updateRef.current;
    if (!update) return;
    setState("downloading");
    setProgress(0);
    setMessage("Downloading and verifying the signed update...");
    let downloaded = 0;
    let total = 0;
    try {
      await update.downloadAndInstall((event) => {
        if (event.event === "Started") {
          total = event.data.contentLength ?? 0;
        } else if (event.event === "Progress") {
          downloaded += event.data.chunkLength;
          if (total > 0) setProgress(Math.min(100, Math.round((downloaded / total) * 100)));
        } else if (event.event === "Finished") {
          setProgress(100);
        }
      });
      setState("restarting");
      setMessage("Update installed. Restarting DJ Agent Desktop...");
      await relaunch();
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "The update could not be installed.");
    }
  }

  return (
    <div className="panel updates-card">
      <div className="updates-heading">
        <div>
          <p className="eyebrow">Signed releases</p>
          <h2>Updates</h2>
          <p>Installed version <strong>v{currentVersion}</strong></p>
        </div>
        <button className="button secondary" onClick={checkForUpdates} disabled={state === "checking" || state === "downloading" || state === "restarting"}>
          <RefreshCw size={16} className={state === "checking" ? "spin" : ""} />
          Check for Updates
        </button>
      </div>
      <div className={`update-status ${state === "error" ? "error" : ""}`}>{message}</div>
      {state === "available" && (
        <div className="release-details">
          <div>
            <strong>Version {availableVersion}</strong>
            {releaseDate && <span>{new Date(releaseDate).toLocaleDateString()}</span>}
          </div>
          <p>{releaseNotes}</p>
          <button className="button primary" onClick={installUpdate}>
            <Download size={16} /> Download and Install
          </button>
        </div>
      )}
      {(state === "downloading" || state === "restarting") && (
        <div className="update-progress">
          <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          <span>{state === "restarting" ? <><RotateCcw size={14} /> Restarting</> : `${progress}%`}</span>
        </div>
      )}
    </div>
  );
}
