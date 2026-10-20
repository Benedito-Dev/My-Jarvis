mod backend;

use std::process::Child;
use std::sync::Mutex;

use tauri::webview::{PermissionKind, PermissionResponse};
use tauri::{Manager, RunEvent};

/// O backend que o app ligou (None se já estava rodando quando o app abriu).
struct BackendLigado(Mutex<Option<Child>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Um clique e tudo liga: o app sobe o backend sozinho (ver backend.rs).
        .setup(|app| {
            app.manage(BackendLigado(Mutex::new(backend::ligar())));
            Ok(())
        })
        // O desbloqueio facial precisa da webcam. No macOS o sistema pergunta ao
        // usuário, mas o WebKitGTK (Linux) nega calado, sem diálogo nenhum — e a
        // tela de bloqueio ficava só "Sem permissão de câmera".
        //
        // Aqui o próprio app responde pelo usuário: ele instalou o Jarvis para ser
        // reconhecido pelo rosto, então a câmera é a função, não uma surpresa.
        // Tudo o mais continua no padrão (negado).
        //
        // O microfone entra pelo mesmo motivo, no passo de ouvir: o WebKitGTK o
        // nega igual. A gravação só acontece enquanto a barra de espaço está
        // segurada — o app não fica escutando sozinho.
        .on_permission_request(|_webview, tipo| match tipo {
            PermissionKind::Camera | PermissionKind::Microphone => PermissionResponse::Allow,
            _ => PermissionResponse::Default,
        })
        .build(tauri::generate_context!())
        .expect("erro ao iniciar o app do Jarvis")
        .run(|app, evento| {
            // Ao fechar, desliga o backend que ELE ligou.
            if let RunEvent::Exit = evento {
                if let Some(estado) = app.try_state::<BackendLigado>() {
                    if let Some(mut processo) = estado.0.lock().unwrap().take() {
                        backend::desligar(&mut processo);
                    }
                }
            }
        });
}
