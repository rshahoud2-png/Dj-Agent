use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

struct EngineProcess(Mutex<Option<CommandChild>>);

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            let sidecar = app
                .shell()
                .sidecar("dj-agent-engine")
                .map_err(|error| format!("Could not prepare local analysis engine: {error}"))?;
            let (mut events, child) = sidecar
                .spawn()
                .map_err(|error| format!("Could not start local analysis engine: {error}"))?;
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
