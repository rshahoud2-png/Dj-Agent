use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct EngineProcess(Mutex<Option<CommandChild>>);

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let sidecar = app
                .shell()
                .sidecar("dj-agent-engine")
                .map_err(|error| format!("Could not prepare local analysis engine: {error}"))?;
            let (_events, child) = sidecar
                .spawn()
                .map_err(|error| format!("Could not start local analysis engine: {error}"))?;
            app.manage(EngineProcess(Mutex::new(Some(child))));
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
