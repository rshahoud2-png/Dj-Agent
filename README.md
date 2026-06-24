# DJ Agent Desktop

DJ Agent Desktop is a standalone Windows 10/11 application for DJs. It scans a local music library, analyzes tracks locally, generates cue points and transition instructions, builds event-ready setlists, and exports CSV or JSON.

Audio never needs to leave the computer. Core functionality does not use Fly.io, Vercel, Supabase, or the DJ Agent web backend.

## Features

- Recursive local scanning for MP3, WAV, FLAC, AIFF/AIF, M4A, AAC, and OGG
- Sequential low-memory audio analysis at 22,050 Hz
- BPM, duration, beat timestamps, 64-bucket energy curve, intro, mix-in, drop, mix-out, loop, and confidence scores
- Durable queue state and failure reporting in SQLite
- Templates for Arabic Wedding, Wedding, Club, Lounge, Bar, Corporate, and Cafe
- Song order, hot cues, transition type, transition bars, compatibility, and plain-language DJ instructions
- CSV and JSON export
- Architecture prepared for rekordbox XML, VirtualDJ `database.xml`, and Serato crate/cue adapters

## Architecture

```text
Tauri v2 Windows shell
  ├─ React + TypeScript + Tailwind UI
  ├─ Native folder/save dialogs
  └─ Bundled Python sidecar (127.0.0.1:17821 only)
       ├─ FastAPI local API
       ├─ librosa / NumPy analysis
       └─ SQLite in %LOCALAPPDATA%\DJ Agent Desktop\dj-agent.db
```

The sidecar accepts local file paths already stored by the scanner. It does not upload or duplicate audio. Analysis is protected by a single-process lock and the React queue waits for each track before starting the next. Arrays are reduced to bounded beat lists and 64 energy buckets, and garbage collection runs after each track.

## Local API

- `GET /health`
- `POST /scan-library`
- `GET /tracks`
- `GET /tracks/{id}/analysis`
- `POST /analyze-track`
- `POST /generate-cues`
- `POST /analyze-transition`
- `POST /generate-set-analysis`
- `POST /setlists/{id}/export`

The service binds only to `127.0.0.1:17821`. Tauri's Content Security Policy only permits the UI to connect to that address.

## Development prerequisites

Install:

1. Node.js 20 or newer
2. Python 3.12 (64-bit)
3. Rust stable with the `x86_64-pc-windows-msvc` target
4. Microsoft Visual Studio Build Tools with **Desktop development with C++**
5. WebView2 Runtime (included on current Windows 10/11)

Python 3.12 is intentionally used for the packaged analysis environment because scientific-audio wheels may lag the newest Python releases.

## Setup

```powershell
npm install
py -3.12 -m venv python-engine\.venv
python-engine\.venv\Scripts\python -m pip install -r python-engine\requirements.txt
```

Run the frontend in a browser with the engine in a second terminal:

```powershell
npm run sidecar:dev
npm run dev
```

Run the complete Tauri desktop app (both command styles are supported):

```powershell
npm run tauri dev
npm run tauri:dev
```

`tauri:dev` packages the Python sidecar first, then launches Tauri.

## Build `DJAgentSetup.exe`

```powershell
npm run tauri build
npm run tauri:build
```

The build script:

1. Creates/reuses `python-engine/.venv`.
2. Installs pinned Python dependencies.
3. Packages the engine as a one-file PyInstaller sidecar.
4. Builds the Tauri v2 NSIS installer.
5. Copies the final installer to:

```text
release\DJAgentSetup.exe
```

Tauri's original NSIS artifact remains under `src-tauri\target\release\bundle\nsis`.

## Database

The SQLite database contains the required tables:

- `tracks`
- `analyses`
- `cue_points`
- `transitions`
- `setlists`
- `settings`

WAL mode is enabled. Tracks left in `analyzing` after an interrupted session are safely returned to `pending` on startup.

## Testing

```powershell
npm test
python python-engine\test_engine.py
npm run build
```

For release verification, also run `npm run tauri:build` on a machine with the Windows Rust/MSVC prerequisites.

## Known limitations

- Audio decoding depends on the codecs supported by `soundfile`/`audioread` in the packaged environment. Some protected or unusual AAC/M4A files may fail cleanly and remain visible in the failed queue.
- BPM and structure analysis are estimates. Low-confidence cues are clearly marked and should be checked before a live performance.
- Key detection, vocal detection, waveform audio playback, and manual cue editing are not included in the first release.
- The v0.1 set builder uses transparent rule-based energy/BPM scoring rather than a hosted AI model.
- Code signing is not configured. Unsigned installers can trigger Windows SmartScreen until a trusted signing certificate is added.

## Roadmap

1. Manual cue editing and waveform playback
2. Musical key/Camelot analysis
3. rekordbox XML export
4. VirtualDJ `database.xml` export
5. Serato crate and cue export
6. Incremental folder watching
7. Optional encrypted cloud sync that never becomes a core dependency

## Source reuse

This repository is separate from `rshahoud2-png/DJ---assistant-`. The original repository was used read-only as a reference for its low-memory librosa approach, cue/transition heuristics, event concepts, and black/gold DJ Agent branding. No changes are required in the web application.
