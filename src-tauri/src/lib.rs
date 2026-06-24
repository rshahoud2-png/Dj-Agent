use std::sync::Mutex;

use serde::Serialize;
use tauri::{Manager, RunEvent, State};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

struct EngineProcess(Mutex<Option<CommandChild>>);

#[derive(Clone, Serialize)]
struct NativeStartupDiagnostics {
    sidecar_exists: bool,
    sidecar_launched: bool,
    sidecar_path: String,
    error: String,
    repair: String,
}

struct StartupDiagnosticsState(Mutex<NativeStartupDiagnostics>);

#[tauri::command]
fn startup_diagnostics(state: State<'_, StartupDiagnosticsState>) -> NativeStartupDiagnostics {
    state
        .0
        .lock()
        .map(|value| value.clone())
        .unwrap_or_else(|_| NativeStartupDiagnostics {
            sidecar_exists: false,
            sidecar_launched: false,
            sidecar_path: String::new(),
            error: "Could not read the native startup diagnostics state.".into(),
            repair: "Close DJ Agent Desktop and launch it again. Reinstall if the problem continues.".into(),
        })
}

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![startup_diagnostics])
        .setup(|app| {
            let candidate = std::env::current_exe()
                .ok()
                .and_then(|path| path.parent().map(|parent| parent.join("dj-agent-engine.exe")));
            let mut diagnostics = NativeStartupDiagnostics {
                sidecar_exists: candidate.as_ref().is_some_and(|path| path.is_file()),
                sidecar_launched: false,
                sidecar_path: candidate
                    .as_ref()
                    .map(|path| path.display().to_string())
                    .unwrap_or_default(),
                error: String::new(),
                repair: String::new(),
            };
            let mut process = None;

            match app.shell().sidecar("dj-agent-engine") {
                Ok(sidecar) => match sidecar.spawn() {
                    Ok((mut events, child)) => {
                        diagnostics.sidecar_exists = true;
                        diagnostics.sidecar_launched = true;
                        process = Some(child);
                        tauri::async_runtime::spawn(async move {
                            while let Some(event) = events.recv().await {
                                match event {
                                    CommandEvent::Stdout(line) => {
                                        println!("[dj-agent-engine] {}", String::from_utf8_lossy(&line));
                                    }
                                    CommandEvent::Stderr(line) => {
                                        eprintln!("[dj-agent-engine] {}", String::from_utf8_lossy(&line));
                                    }
                                    CommandEvent::Error(error) => {
                                        eprintln!("[dj-agent-engine] process error: {error}");
                                    }
                                    CommandEvent::Terminated(status) => {
                                        eprintln!("[dj-agent-engine] terminated: {status:?}");
                                    }
                                    _ => {}
                                }
                            }
                        });
                    }
                    Err(error) => {
                        diagnostics.error = format!("The bundled analysis engine could not launch: {error}");
                        diagnostics.repair =
                            "Reinstall DJ Agent Desktop from the latest official DJAgentSetup.exe. Antivirus software may have quarantined dj-agent-engine.exe.".into();
                    }
                },
                Err(error) => {
                    diagnostics.error = format!("The bundled analysis engine could not be located: {error}");
                    diagnostics.repair =
                        "Reinstall DJ Agent Desktop from the latest official DJAgentSetup.exe.".into();
                }
            }

            if !diagnostics.sidecar_exists && diagnostics.error.is_empty() {
                diagnostics.error = "The bundled analysis engine file is missing.".into();
                diagnostics.repair =
                    "Reinstall DJ Agent Desktop and check antivirus quarantine history for dj-agent-engine.exe.".into();
            }

            app.manage(StartupDiagnosticsState(Mutex::new(diagnostics)));
            app.manage(EngineProcess(Mutex::new(process)));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building DJ Agent Desktop");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            if let Some(process) = app_handle.try_state::<EngineProcess>() {
                if let Ok(mut child) = process.0.lock() {
                    if let Some(child) = child.take() {
                        let _ = child.kill();
                    }
                }
            }
        }
    });
}
