import { invoke } from "@tauri-apps/api/core";
import { AlertTriangle, CheckCircle2, LoaderCircle, RefreshCw, Wrench } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { engineApi } from "../lib/api";
import type { HealthResponse, NativeStartupDiagnostics, RuntimeCheck } from "../lib/types";

const wait = (milliseconds: number) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export function StartupDiagnostics({ onReady }: { onReady: (health: HealthResponse) => Promise<void> }) {
  const [checks, setChecks] = useState<RuntimeCheck[]>([]);
  const [running, setRunning] = useState(true);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const runDiagnostics = useCallback(async () => {
    setRunning(true);
    setHealth(null);
    const results: RuntimeCheck[] = [];
    const inTauri = "__TAURI_INTERNALS__" in window;

    if (inTauri) {
      try {
        const native = await invoke<NativeStartupDiagnostics>("startup_diagnostics");
        results.push({
          key: "sidecar_exists",
          label: "Python analysis sidecar included",
          ok: native.sidecar_exists,
          details: native.sidecar_path || native.error || "Bundled sidecar location resolved by Tauri.",
          repair: native.repair,
        });
        results.push({
          key: "sidecar_launched",
          label: "Python analysis sidecar launches",
          ok: native.sidecar_launched,
          details: native.sidecar_launched ? "The packaged engine process started without requiring system Python." : native.error,
          repair: native.repair,
        });
      } catch (error) {
        results.push({
          key: "native",
          label: "Native startup checks",
          ok: false,
          details: error instanceof Error ? error.message : String(error),
          repair: "Restart the app. If this continues, reinstall the latest DJAgentSetup.exe.",
        });
      }
    }
    setChecks([...results]);

    let response: HealthResponse | null = null;
    for (let attempt = 0; attempt < 40; attempt += 1) {
      try {
        response = await engineApi.health();
        break;
      } catch {
        await wait(500);
      }
    }
    results.push({
      key: "health",
      label: "Local engine health responds",
      ok: response?.status === "ok",
      details: response ? "http://127.0.0.1:17821/health returned OK." : "The local-only health endpoint did not respond.",
      repair: "Restart DJ Agent Desktop. If the engine is blocked, allow it in antivirus or reinstall the app.",
    });
    setChecks([...results]);

    if (response) {
      try {
        const diagnostics = await engineApi.diagnostics();
        results.push(...diagnostics.checks);
      } catch (error) {
        results.push({
          key: "runtime",
          label: "Engine runtime checks",
          ok: false,
          details: error instanceof Error ? error.message : String(error),
          repair: "Reinstall DJ Agent Desktop from the latest official release.",
        });
      }
    }

    setChecks(results);
    setHealth(response);
    setRunning(false);
  }, []);

  useEffect(() => {
    void runDiagnostics();
  }, [runDiagnostics]);

  const failed = checks.filter((check) => !check.ok);
  const ready = !running && health && failed.length === 0;

  return (
    <main className="diagnostics-screen">
      <section className="panel diagnostics-panel">
        <div className="diagnostics-title">
          <div className="diagnostics-mark"><Wrench size={25} /></div>
          <div>
            <p className="eyebrow">Clean Windows startup check</p>
            <h1>DJ Agent Diagnostics</h1>
            <p>Verifying the bundled audio engine, codecs, native libraries, and local storage.</p>
          </div>
        </div>

        <div className="diagnostics-list">
          {checks.map((check) => (
            <div className={`diagnostic-row ${check.ok ? "passed" : "failed"}`} key={check.key}>
              {check.ok ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
              <div>
                <strong>{check.label}</strong>
                <p>{check.details}</p>
                {!check.ok && check.repair && <small>Repair: {check.repair}</small>}
              </div>
            </div>
          ))}
          {running && (
            <div className="diagnostic-row checking">
              <LoaderCircle className="spin" size={20} />
              <div><strong>Running checks</strong><p>The first launch can take longer while PyInstaller extracts the engine.</p></div>
            </div>
          )}
        </div>

        <div className="diagnostics-actions">
          {!running && failed.length > 0 && <p>{failed.length} required check{failed.length === 1 ? "" : "s"} failed. Follow the repair instructions above.</p>}
          {ready && <p>All required local runtime checks passed.</p>}
          <div>
            {!running && <button className="button secondary" onClick={runDiagnostics}><RefreshCw size={16} /> Run Again</button>}
            {ready && health && <button className="button primary" onClick={() => void onReady(health)}>Open DJ Agent</button>}
          </div>
        </div>
      </section>
    </main>
  );
}
