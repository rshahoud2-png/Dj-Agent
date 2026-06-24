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
- rekordbox XML and VirtualDJ `database.xml` export adapters
- Serato M3U8 crate bridge with a JSON cue manifest and a boundary for future native crate writing
- Signed in-app updates from GitHub Releases with release notes and automatic restart

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
- `GET /integrations`
- `POST /setlists/{id}/export-dj`

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

1. Validates Node.js, Python 3.12, Rust, Cargo, and the MSVC Rust target.
2. Generates Windows icons from `assets/app-icon.svg` when needed.
3. Creates/reuses `python-engine/.venv`.
4. Installs pinned Python dependencies.
5. Packages the engine as a one-file PyInstaller sidecar.
6. Launches the frozen sidecar and verifies its local `/health` endpoint.
7. Builds the Tauri v2 NSIS installer without a console window.
8. Copies the final installer to:

```text
release\DJAgentSetup.exe
```

Tauri's original NSIS artifact remains under `src-tauri\target\release\bundle\nsis`.

Every push to `main` also runs `.github/workflows/windows-installer.yml` on a Windows runner. The workflow validates the frontend and Python engine, builds the sidecar and NSIS installer, and uploads a `DJAgentSetup` artifact containing `DJAgentSetup.exe`.

## Live updates

DJ Agent Desktop 0.2.0 and newer can check GitHub Releases from **Settings > Updates**, display release notes, download a signed installer, install it in passive mode, and restart automatically. Release builds require the private Tauri updater key in the `TAURI_SIGNING_PRIVATE_KEY` GitHub Actions secret.

See [docs/updates.md](docs/updates.md) for version bumping, one-time signing setup, publishing a tagged release, and the installed update flow.

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
- Serato export currently produces a portable M3U8 crate and cue manifest. Native binary `.crate` writing remains future work.
- rekordbox and VirtualDJ XML adapters are intentionally isolated and should be validated against the exact DJ software version used in production before overwriting any vendor database.
- Key detection, vocal detection, waveform audio playback, and manual cue editing are not included in the first release.
- The v0.1 set builder uses transparent rule-based energy/BPM scoring rather than a hosted AI model.
- Tauri updater packages are cryptographically signed. Windows Authenticode signing is separate and is not yet configured, so first-time installers can still trigger SmartScreen.

## Roadmap

1. Manual cue editing and waveform playback
2. Musical key/Camelot analysis
3. Native Serato binary crate writing
4. Incremental folder watching
5. Optional encrypted cloud sync that never becomes a core dependency

## DJ software integration architecture

Vendor exports implement a small adapter contract in `python-engine/app/integrations.py`. Each adapter declares its key, display name, extension, and export method. Setlist analysis remains vendor-neutral; adapters consume the stored setlist payload only at export time.

- `rekordbox`: Pioneer DJ XML collection, playlist, BPM, and position marks
- `virtualdj`: VirtualDJ-style song records, scan BPM, cue POIs, and loop POI
- `serato`: UTF-8 M3U8 crate bridge plus `.cues.json` manifest

This separation keeps proprietary formats out of the analysis and database layers and allows future adapters to be registered without changing the core engine.

## Source reuse

This repository is separate from `rshahoud2-png/DJ---assistant-`. The original repository was used read-only as a reference for its low-memory librosa approach, cue/transition heuristics, event concepts, and black/gold DJ Agent branding. No changes are required in the web application.
