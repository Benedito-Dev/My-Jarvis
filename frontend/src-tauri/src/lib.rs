use tauri::webview::{PermissionKind, PermissionResponse};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // O desbloqueio facial precisa da webcam. No macOS o sistema pergunta ao
        // usuário, mas o WebKitGTK (Linux) nega calado, sem diálogo nenhum — e a
        // tela de bloqueio ficava só "Sem permissão de câmera".
        //
        // Aqui o próprio app responde pelo usuário: ele instalou o Jarvis para ser
        // reconhecido pelo rosto, então a câmera é a função, não uma surpresa.
        // Tudo o mais continua no padrão (negado).
        .on_permission_request(|_webview, tipo| match tipo {
            PermissionKind::Camera => PermissionResponse::Allow,
            _ => PermissionResponse::Default,
        })
        .run(tauri::generate_context!())
        .expect("erro ao iniciar o app do Jarvis");
}
