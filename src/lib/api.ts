import type { DjExportTarget, DjIntegration, EventType, HealthResponse, RuntimeDiagnostics, Setlist, Track, TrackAnalysis } from "./types";

const ENGINE_URL = import.meta.env.VITE_ENGINE_URL ?? "http://127.0.0.1:17821";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${ENGINE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? payload.error ?? "Local engine request failed");
  }
  return response.json() as Promise<T>;
}

export const engineApi = {
  health: () => request<HealthResponse>("/health"),
  diagnostics: () => request<RuntimeDiagnostics>("/diagnostics"),
  scanLibrary: (folder: string) =>
    request<{ discovered: number; added: number; updated: number }>("/scan-library", {
      method: "POST",
      body: JSON.stringify({ folder }),
    }),
  listTracks: () => request<Track[]>("/tracks"),
  getAnalysis: (trackId: number) => request<TrackAnalysis>(`/tracks/${trackId}/analysis`),
  analyzeTrack: (trackId: number) =>
    request<TrackAnalysis>("/analyze-track", {
      method: "POST",
      body: JSON.stringify({ track_id: trackId }),
    }),
  generateCues: (trackId: number) =>
    request<TrackAnalysis>("/generate-cues", {
      method: "POST",
      body: JSON.stringify({ track_id: trackId }),
    }),
  generateSetlist: (eventType: EventType, eventDuration: number, name: string) =>
    request<Setlist>("/generate-set-analysis", {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        event_duration: eventDuration,
        name,
      }),
    }),
  exportSetlist: (setlistId: number, format: "csv" | "json", destination: string) =>
    request<{ path: string }>(`/setlists/${setlistId}/export`, {
      method: "POST",
      body: JSON.stringify({ format, destination }),
    }),
  integrations: () => request<DjIntegration[]>("/integrations"),
  exportDjSoftware: (setlistId: number, target: DjExportTarget, destination: string) =>
    request<{ paths: string[] }>(`/setlists/${setlistId}/export-dj`, {
      method: "POST",
      body: JSON.stringify({ target, destination }),
    }),
};
