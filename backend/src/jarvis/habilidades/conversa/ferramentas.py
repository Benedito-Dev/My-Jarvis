"""As "mãos" do Jarvis: ferramentas que a IA pode decidir usar.

Cada ferramenta tem um nome, uma descrição (é por ela que a IA sabe quando usar)
e os parâmetros que espera, no formato de "function calling" do OpenRouter.
Nova ferramenta = nova função aqui que devolve uma `Ferramenta`.

Além do texto para a IA, cada resultado pode trazer um `cartao`: os mesmos
dados, organizados para a tela mostrar enquanto o Jarvis fala. Todo cartão tem
`tipo` (clima, lembretes, pesquisa, notas, conta, abrir), `rotulo` e `titulo`.
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from jarvis.habilidades.calculadora import conta
from jarvis.habilidades.clima import previsao
from jarvis.habilidades.conversa.comandos import as_horas
from jarvis.habilidades.lembretes.agenda import Agenda, LembreteInvalidoError
from jarvis.habilidades.notas.caderno import Caderno, NotaInvalidaError
from jarvis.habilidades.pesquisa import web
from jarvis.nucleo import sistema


@dataclass(frozen=True)
class Resultado:
    """O que a ferramenta fez.

    - `para_ia`: o resultado contado à IA, se ela precisar continuar a resposta;
    - `fala`: uma confirmação já pronta para falar. Se toda ferramenta usada
      trouxer a sua, não é preciso voltar à IA (~2 s a menos).
    """

    para_ia: str
    fala: str | None = None
    cartao: dict | None = None


@dataclass(frozen=True)
class Ferramenta:
    nome: str
    descricao: str
    parametros: dict  # JSON Schema
    executar: Callable[[dict], Resultado]


def no_formato_da_ia(ferramentas: Iterable[Ferramenta]) -> list[dict]:
    """A lista de ferramentas como a IA espera receber."""
    return [
        {
            "type": "function",
            "function": {
                "name": f.nome,
                "description": f.descricao,
                "parameters": f.parametros,
            },
        }
        for f in ferramentas
    ]


def executar(ferramentas: Iterable[Ferramenta], nome: str, argumentos: str) -> Resultado:
    """Roda a ferramenta que a IA pediu. Erros viram resultado, para a IA explicar."""
    por_nome = {f.nome: f for f in ferramentas}
    if nome not in por_nome:
        return Resultado(para_ia=f"Erro: não existe a ferramenta {nome!r}.")
    try:
        parametros = json.loads(argumentos or "{}")
    except json.JSONDecodeError:
        return Resultado(para_ia="Erro: os parâmetros não vieram em JSON válido.")
    try:
        return por_nome[nome].executar(parametros)
    except (KeyError, TypeError, ValueError) as erro:
        return Resultado(para_ia=f"Erro ao usar {nome}: {erro}")


# --- Lembretes ------------------------------------------------------------------


def lembrete(agenda: Agenda) -> Ferramenta:
    def criar(parametros: dict) -> Resultado:
        try:
            criado = agenda.criar(float(parametros["daqui_a_minutos"]), parametros["texto"])
        except LembreteInvalidoError as erro:
            return Resultado(para_ia=f"Não agendado: {erro}")
        horario = as_horas(criado.quando)
        return Resultado(
            para_ia=f"Lembrete agendado para {horario}: {criado.texto}.",
            fala=f"Certo. Te aviso {horario}.",
            cartao=_cartao_lembretes("Lembrete criado", [criado]),
        )

    return Ferramenta(
        nome="criar_lembrete",
        descricao=(
            "Agenda um lembrete que o Jarvis fala em voz alta depois de alguns minutos. "
            "Use quando pedirem para lembrar ou avisar de algo mais tarde. "
            "Para um horário (ex.: às 10 e meia), calcule os minutos a partir de agora."
        ),
        parametros={
            "type": "object",
            "properties": {
                "daqui_a_minutos": {
                    "type": "number",
                    "description": "Em quantos minutos avisar (de 1 a 1440).",
                },
                "texto": {
                    "type": "string",
                    "description": "O que lembrar, curto (ex.: 'ligar pro dentista').",
                },
            },
            "required": ["daqui_a_minutos", "texto"],
        },
        executar=criar,
    )


def listar_lembretes(agenda: Agenda) -> Ferramenta:
    def listar(_parametros: dict) -> Resultado:
        pendentes = agenda.pendentes()
        if not pendentes:
            return Resultado(para_ia="Nenhum lembrete pendente.")
        itens = "; ".join(f"{as_horas(lem.quando)}: {lem.texto}" for lem in pendentes)
        return Resultado(
            para_ia=f"Lembretes pendentes: {itens}.",
            cartao=_cartao_lembretes("Lembretes", pendentes),
        )

    return Ferramenta(
        nome="listar_lembretes",
        descricao="Lista os lembretes que ainda vão tocar. Use quando perguntarem pelos lembretes.",
        parametros={"type": "object", "properties": {}},
        executar=listar,
    )


def _cartao_lembretes(rotulo: str, lembretes) -> dict:
    quantos = len(lembretes)
    return {
        "tipo": "lembretes",
        "rotulo": rotulo,
        "titulo": "1 lembrete" if quantos == 1 else f"{quantos} lembretes",
        "itens": [{"hora": f"{lem.quando:%H:%M}", "texto": lem.texto} for lem in lembretes],
    }


# --- Pesquisa na web --------------------------------------------------------------


CARTAO_MAXIMO_DE_ACHADOS = 3


def pesquisar_web(buscar: web.Buscar = web._buscar_ddgs) -> Ferramenta:
    def executar_busca(parametros: dict) -> Resultado:
        noticias = bool(parametros.get("noticias"))
        try:
            achados = web.pesquisar(parametros["consulta"], noticias, buscar=buscar)
        except web.PesquisaIndisponivelError as erro:
            return Resultado(para_ia=f"A busca falhou ({erro}). Diga que não conseguiu pesquisar.")
        cartao = {
            "tipo": "pesquisa",
            "rotulo": "Notícias" if noticias else "Pesquisa",
            "titulo": parametros["consulta"],
            "itens": [
                {"titulo": a.titulo, "resumo": a.resumo, "fonte": a.fonte}
                for a in achados[:CARTAO_MAXIMO_DE_ACHADOS]
            ],
        }
        return Resultado(para_ia=web.para_a_ia(achados), cartao=cartao if achados else None)

    return Ferramenta(
        nome="pesquisar_web",
        descricao=(
            "Pesquisa na internet. Use para fatos atuais ou que você não sabe com certeza: "
            "resultados de jogos, notícias, preços, eventos, pessoas. Resuma o que achar "
            "em poucas frases faladas, sem ler links."
        ),
        parametros={
            "type": "object",
            "properties": {
                "consulta": {"type": "string", "description": "O que pesquisar, em português."},
                "noticias": {
                    "type": "boolean",
                    "description": "true para buscar só notícias recentes.",
                },
            },
            "required": ["consulta"],
        },
        executar=executar_busca,
    )


# --- Clima ---------------------------------------------------------------------------


def clima(obter: previsao.ObterJson = previsao._obter_json) -> Ferramenta:
    def executar_clima(parametros: dict) -> Resultado:
        cidade = (parametros.get("cidade") or "").strip() or previsao.cidade_padrao()
        if not cidade:
            return Resultado(para_ia="Não sei a cidade. Pergunte ao usuário de qual cidade.")
        try:
            lugar, dados = previsao.consultar(cidade, obter=obter)
        except previsao.ClimaIndisponivelError as erro:
            return Resultado(para_ia=str(erro))
        return Resultado(
            para_ia=previsao.resumir(lugar, dados), cartao=previsao.cartao(lugar, dados)
        )

    return Ferramenta(
        nome="clima",
        descricao=(
            "Tempo agora e previsão de hoje, amanhã e depois de amanhã: temperatura, "
            "chuva, céu. Sem cidade, usa a cidade padrão do usuário."
        ),
        parametros={
            "type": "object",
            "properties": {
                "cidade": {"type": "string", "description": "Cidade (opcional)."},
            },
        },
        executar=executar_clima,
    )


# --- Abrir apps e sites ---------------------------------------------------------


def abrir_site(rodar=None) -> Ferramenta:
    def executar_site(parametros: dict) -> Resultado:
        try:
            comando = sistema.comando_abrir_site(parametros["endereco"])
            sistema.abrir(comando, **({"rodar": rodar} if rodar else {}))
        except sistema.NaoConsigoAbrirError as erro:
            return Resultado(para_ia=str(erro))
        return Resultado(
            para_ia="Site aberto.",
            fala="Abrindo.",
            cartao={"tipo": "abrir", "rotulo": "Abrindo site", "titulo": parametros["endereco"]},
        )

    return Ferramenta(
        nome="abrir_site",
        descricao=(
            "Abre um site no navegador. Também serve para buscas em sites, montando o "
            "endereço (ex.: youtube.com/results?search_query=lofi)."
        ),
        parametros={
            "type": "object",
            "properties": {
                "endereco": {"type": "string", "description": "Ex.: 'youtube.com'."},
            },
            "required": ["endereco"],
        },
        executar=executar_site,
    )


def abrir_app(rodar=None) -> Ferramenta:
    def executar_app(parametros: dict) -> Resultado:
        nome = parametros["nome"].strip()
        try:
            comando = sistema.comando_abrir_app(nome)
            sistema.abrir(comando, **({"rodar": rodar} if rodar else {}))
        except sistema.NaoConsigoAbrirError as erro:
            return Resultado(para_ia=str(erro))
        return Resultado(
            para_ia=f"{nome} aberto.",
            fala=f"Abrindo o {nome}.",
            cartao={"tipo": "abrir", "rotulo": "Abrindo app", "titulo": nome},
        )

    return Ferramenta(
        nome="abrir_app",
        descricao="Abre um aplicativo instalado no computador (ex.: Spotify, Calculadora).",
        parametros={
            "type": "object",
            "properties": {
                "nome": {"type": "string", "description": "Nome do app, como aparece no sistema."},
            },
            "required": ["nome"],
        },
        executar=executar_app,
    )


# --- Notas ------------------------------------------------------------------------


def anotar(caderno: Caderno) -> Ferramenta:
    def executar_anotar(parametros: dict) -> Resultado:
        try:
            nota = caderno.anotar(parametros["texto"])
        except NotaInvalidaError as erro:
            return Resultado(para_ia=f"Não anotado: {erro}")
        return Resultado(
            para_ia=f"Anotado: {nota.texto}",
            fala="Anotado.",
            cartao={
                "tipo": "notas",
                "rotulo": "Anotado",
                "titulo": "Nova nota",
                "itens": [nota.texto],
            },
        )

    return Ferramenta(
        nome="anotar",
        descricao="Guarda uma anotação do usuário para depois (ex.: 'anota: comprar café').",
        parametros={
            "type": "object",
            "properties": {"texto": {"type": "string", "description": "O que anotar."}},
            "required": ["texto"],
        },
        executar=executar_anotar,
    )


CARTAO_MAXIMO_DE_NOTAS = 5


def ler_notas(caderno: Caderno) -> Ferramenta:
    def executar_ler(_parametros: dict) -> Resultado:
        notas = caderno.listar()
        if not notas:
            return Resultado(para_ia="Não há anotações.")
        recentes = [n.texto for n in notas[-20:]]
        return Resultado(
            para_ia="Anotações, da mais antiga à mais nova: " + "; ".join(recentes),
            cartao={
                "tipo": "notas",
                "rotulo": "Notas",
                "titulo": f"{len(notas)} anotações" if len(notas) != 1 else "1 anotação",
                "itens": recentes[-CARTAO_MAXIMO_DE_NOTAS:],
            },
        )

    return Ferramenta(
        nome="ler_notas",
        descricao="Lê as anotações guardadas. Use quando perguntarem o que foi anotado.",
        parametros={"type": "object", "properties": {}},
        executar=executar_ler,
    )


# --- Calculadora --------------------------------------------------------------------


def calcular() -> Ferramenta:
    def executar_conta(parametros: dict) -> Resultado:
        try:
            resultado = conta.calcular(parametros["expressao"])
        except conta.ContaInvalidaError as erro:
            return Resultado(para_ia=str(erro))
        expressao = parametros["expressao"]
        formatado = conta.formatar(resultado)
        return Resultado(
            para_ia=f"{expressao} = {formatado}",
            cartao={
                "tipo": "conta",
                "rotulo": "Cálculo",
                "titulo": formatado.replace(".", ","),  # na tela, vírgula decimal
                "expressao": expressao,
            },
        )

    return Ferramenta(
        nome="calcular",
        descricao=(
            "Faz contas exatas. Use SEMPRE que a resposta depender de uma conta "
            "(porcentagem, divisão, juros...), em vez de calcular de cabeça."
        ),
        parametros={
            "type": "object",
            "properties": {
                "expressao": {
                    "type": "string",
                    "description": "Expressão com números e + - * / % ** (ex.: '3480 * 17 / 100').",
                },
            },
            "required": ["expressao"],
        },
        executar=executar_conta,
    )
