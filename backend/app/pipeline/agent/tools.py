from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import select

from app.features.materials.models import Material
from app.infra.db import SessionLocal
from app.pipeline.params import AnswerParams
from app.pipeline.retrieval import kept, relevance, search_two_stages

# Limite de texto devolvido pela ferramenta de resumo. Materiais longos
# (uma aula de duas horas transcrita) estourariam a janela do modelo.
_MAX_SUMMARY_CHARS = 12000

NOTHING_FOUND = (
    "NADA RELEVANTE ENCONTRADO no material para essa pergunta. "
    "Não responda por conhecimento próprio."
)


def build_tools(material_ids: list[UUID], params: AnswerParams, trace: dict) -> list:
    """Monta as ferramentas do agente já presas aos materiais de um chat.

    Os material_ids NÃO são parâmetro de ferramenta: são fixados aqui, por fora.
    Assim o modelo não tem como pedir material que não pertence ao chat — a
    restrição é estrutural, não depende do comportamento do LLM.

    Todas as ferramentas leem apenas esses materiais. Nenhuma tem acesso a
    conhecimento externo.

    `trace` registra o que o agente fez, para o painel "entender a resposta":
    trace["steps"]     cada ferramenta chamada, na ordem, com a entrada
    trace["searches"]  cada busca, com todos os candidatos e suas notas
    É criado por requisição, nunca compartilhado.
    """

    def log(tool_name: str, tool_input: str) -> None:
        trace["steps"].append({"tool": tool_name, "input": tool_input})

    async def load_materials() -> list[Material]:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Material).where(Material.id.in_(material_ids))
            )
            return list(result.scalars().all())

    @tool
    async def buscar_no_material(pergunta: str) -> str:
        """Busca trechos do material que respondam a uma pergunta.

        Use para qualquer dúvida sobre o conteúdo. Se a pergunta tiver mais de
        um assunto, chame uma vez para cada assunto.
        """
        log("buscar_no_material", pergunta)
        candidates = await search_two_stages(material_ids, pergunta, params)
        trace["searches"].append({"query": pergunta, "candidates": candidates})

        usados = kept(candidates)
        if not usados:
            return NOTHING_FOUND
        partes = [
            f"[trecho {i + 1} | relevância {relevance(c):.2f}]\n{c['text']}"
            for i, c in enumerate(usados)
        ]
        return "\n\n".join(partes)

    @tool
    async def listar_topicos() -> str:
        """Lista os materiais disponíveis e sobre o que cada um trata.

        Use quando perguntarem o que o material cobre, ou quando precisar
        saber que assuntos existem antes de buscar.
        """
        log("listar_topicos", "")
        materiais = await load_materials()
        if not materiais:
            return "Este chat ainda não tem material."

        linhas = []
        for m in materiais:
            inicio = (m.text or "")[:300].replace("\n", " ").strip()
            linhas.append(f"- {m.filename} ({m.media_type}): {inicio}...")
        return "\n".join(linhas)

    @tool
    async def resumir_material(nome_do_material: str = "") -> str:
        """Devolve o texto completo de um material, para resumir.

        Passe o nome do arquivo. Deixe vazio para pegar o primeiro material.
        Use quando pedirem resumo ou visão geral, não para dúvidas pontuais.
        """
        log("resumir_material", nome_do_material)
        materiais = await load_materials()
        if nome_do_material:
            materiais = [
                m for m in materiais if nome_do_material.lower() in m.filename.lower()
            ]
        if not materiais:
            return "Material não encontrado neste chat."
        material = materiais[0]
        if not material.text:
            return f"O material {material.filename} ainda não foi processado."

        texto = material.text
        if len(texto) > _MAX_SUMMARY_CHARS:
            texto = texto[:_MAX_SUMMARY_CHARS] + "\n[...texto truncado...]"
        return f"Material: {material.filename}\n\n{texto}"

    @tool
    async def pedir_esclarecimento(pergunta_ao_usuario: str) -> str:
        """Pede que o usuário esclareça uma pergunta ambígua ou vaga demais.

        Use apenas quando a pergunta não tiver assunto identificável — não use
        para fugir de perguntas difíceis, nem quando a busca já traz trechos
        úteis, nem para perguntas claras sobre assuntos que parecem fora do
        material (nesses casos, busque).
        """
        log("pedir_esclarecimento", pergunta_ao_usuario)
        return (
            "Devolva exatamente esta pergunta ao usuário, sem acrescentar nada: "
            f"{pergunta_ao_usuario}"
        )

    return [
        buscar_no_material,
        listar_topicos,
        resumir_material,
        pedir_esclarecimento,
    ]
