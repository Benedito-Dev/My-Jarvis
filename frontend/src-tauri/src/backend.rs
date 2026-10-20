//! O app liga o backend (o "cérebro" em Python) sozinho: sem terminal.
//!
//! Ao abrir: se o backend já responde na porta 8765, só usa. Se não, liga
//! `python -m jarvis servidor` na pasta `backend/` do projeto. Ao fechar,
//! desliga apenas o que ELE ligou (um backend aberto à mão continua rodando).
//!
//! Funciona igual nos três sistemas: o que muda é só onde fica o Python do
//! ambiente (`.venv/bin/python` ou `.venv\Scripts\python.exe`).

use std::fs::OpenOptions;
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::Duration;

const PORTA: u16 = 8765;

/// A pasta `backend/` do projeto. `JARVIS_BACKEND` troca; o padrão é a pasta
/// ao lado do frontend, de onde este app foi compilado.
pub fn pasta_backend() -> PathBuf {
    if let Ok(pasta) = std::env::var("JARVIS_BACKEND") {
        return PathBuf::from(pasta);
    }
    Path::new(env!("CARGO_MANIFEST_DIR")).join("..").join("..").join("backend")
}

/// Alguém já responde na porta do backend?
pub fn ja_esta_rodando() -> bool {
    let endereco = SocketAddr::from(([127, 0, 0, 1], PORTA));
    TcpStream::connect_timeout(&endereco, Duration::from_millis(300)).is_ok()
}

/// O comando que liga o servidor: o Python do `.venv` do projeto (instalado
/// pelo `uv sync`). Sem ele, cai para `uv run`, que monta o ambiente antes.
fn comando_do_servidor(pasta: &Path) -> Command {
    let python = if cfg!(windows) {
        pasta.join(".venv").join("Scripts").join("python.exe")
    } else {
        pasta.join(".venv").join("bin").join("python")
    };
    let mut comando = if python.exists() {
        Command::new(python)
    } else {
        // Um app aberto pelo Finder não herda o PATH do terminal: procura o uv
        // nos lugares onde o instalador costuma deixar.
        let mut uv = Command::new(onde_esta_o_uv());
        uv.args(["run", "python"]);
        uv
    };
    comando.args(["-m", "jarvis", "servidor"]).current_dir(pasta);
    comando
}

fn onde_esta_o_uv() -> PathBuf {
    let casa = std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .unwrap_or_default();
    let nome = if cfg!(windows) { "uv.exe" } else { "uv" };
    let candidatos = [
        PathBuf::from(&casa).join(".local").join("bin").join(nome),
        PathBuf::from(&casa).join(".cargo").join("bin").join(nome),
        PathBuf::from("/opt/homebrew/bin").join(nome),
        PathBuf::from("/usr/local/bin").join(nome),
    ];
    candidatos
        .into_iter()
        .find(|caminho| caminho.exists())
        .unwrap_or_else(|| PathBuf::from(nome)) // último recurso: o PATH
}

/// Liga o backend, se ainda não estiver rodando. Devolve o processo que ligou,
/// ou None se já havia um (ou se não deu para ligar; o app mostra o aviso).
pub fn ligar() -> Option<Child> {
    if ja_esta_rodando() {
        return None;
    }
    let pasta = pasta_backend();
    // A saída do servidor vai para dados/servidor.log (fora do git), para dar
    // para ver o que houve quando não há terminal aberto.
    let pasta_dados = pasta.join("dados");
    let _ = std::fs::create_dir_all(&pasta_dados);
    let log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(pasta_dados.join("servidor.log"))
        .ok()?;
    let mut comando = comando_do_servidor(&pasta);
    comando
        .stdout(Stdio::from(log.try_clone().ok()?))
        .stderr(Stdio::from(log))
        .env("PYTHONUNBUFFERED", "1");
    match comando.spawn() {
        Ok(processo) => Some(processo),
        Err(erro) => {
            eprintln!("Não consegui ligar o backend em {}: {erro}", pasta.display());
            None
        }
    }
}

/// Desliga o backend que o app ligou. No Mac e no Linux pede com educação
/// (SIGTERM, para o servidor fechar direito); no Windows, encerra.
pub fn desligar(processo: &mut Child) {
    #[cfg(unix)]
    {
        let _ = Command::new("kill").arg(processo.id().to_string()).status();
        for _ in 0..30 {
            if let Ok(Some(_)) = processo.try_wait() {
                return;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
    }
    let _ = processo.kill();
    let _ = processo.wait();
}
