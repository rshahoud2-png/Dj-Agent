export type TrackStatus = "pending" | "analyzing" | "complete" | "failed";

export interface HealthResponse {
  status: string;
  database_path: string;
}

export interface RuntimeCheck {
  key: string;
  label: string;
  ok: boolean;
  details: string;
  repair: string;
}

export interface RuntimeDiagnostics {
  status: "ok" | "error";
  checks: RuntimeCheck[];
}

export interface NativeStartupDiagnostics {
  sidecar_exists: boolean;
  sidecar_launched: boolean;
  sidecar_path: string;
  error: string;
  repair: string;
}

export interface CuePoint {
  id?: number;
  label: string;
  name: string;
  timestamp: number;
  reason: string;
  confidence: number;
}

export interface LoopCue {
  start: number;
  end: number;
  bars: number;
  reason: string;
  confidence: number;
}

export interface TrackAnalysis {
  track_id: number;
  path: string;
  title: string;
  artist: string;
  estimated_bpm: number;
  duration: number;
  beat_timestamps: number[];
  energy_curve: number[];
  intro_cue: number;
  mix_in_cue: number;
  drop_cue: number;
  mix_out_cue: number;
  loop_cue: LoopCue;
  confidence_scores: Record<string, number>;
  analysis_confidence: number;
  warnings: string[];
  hot_cues: CuePoint[];
}

export type DjExportTarget = "rekordbox" | "virtualdj" | "serato";

export interface DjIntegration {
  key: DjExportTarget;
  name: string;
  extension: string;
  description: string;
}

export interface Track {
  id: number;
  path: string;
  filename: string;
  title: string;
  artist: string;
  album: string;
  extension: string;
  file_size: number;
  modified_at: number;
  status: TrackStatus;
  error?: string | null;
  bpm?: number | null;
  duration?: number | null;
  analysis_confidence?: number | null;
}

export interface Transition {
  from_track_id: number;
  to_track_id: number;
  compatibility_score: number;
  recommended_transition_type: string;
  suggested_transition_length_bars: number;
  dj_performance_instruction: string;
  warnings: string[];
}

export interface SetlistItem {
  position: number;
  section: string;
  track: TrackAnalysis;
  transition?: Transition | null;
  cue_notes: string[];
  warnings: string[];
}

export interface Setlist {
  id: number;
  name: string;
  event_type: string;
  event_duration: number;
  confidence_score: number;
  items: SetlistItem[];
  warnings: string[];
}

export type EventType =
  | "Arabic Wedding"
  | "Wedding"
  | "Club"
  | "Lounge"
  | "Bar"
  | "Corporate"
  | "Cafe";
