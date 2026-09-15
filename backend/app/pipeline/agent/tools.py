from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import select

from app.features.materials.models import Material
from app.infra.config import settings
from app.infra.db import SessionLocal
from app.pipeline.retrieval import search_and_rerank

# Limite de texto devolvido pela ferramenta de resumo. Materiais longos
# (uma aula de duas horas transcrita) estourariam a janela do modelo.
_MAX_SUMMARY_CHARS = 12000


def build_tools(course_id: UUID, sources_out: list[dict]) -> list:
    """Monta as ferramentas do agente já presas a um curso.

    O course_id NÃO é parâmetro de ferramenta: ele é fixado aqui, por fora.
    Assim o modelo não tem como pedir material de outro curso — a restrição
    é estrutural, não depende do comportamento do LLM.

    Todas as ferramentas leem apenas o material deste curso. Nenhuma tem
    acesso a conhecimento externo.

    `sources_out` acumula os trechos efetivamente usados, para a resposta
    poder citar as fontes. É criado por requisição, nunca compartilhado.
    """

    @tool
    async def buscar_no_material(pergunta: str) -> str:
        """Busca trechos do material do curso que respondam a uma pergunta.

        Use para qualquer dúvida sobre o conteúdo. Se a pergunta tiver mais de
        um assunto, chame uma vez para cada assunto.
        """
        results = await search_and_rerank(course_id, pergunta)
        relevantes = [
            (doc, score)
            for doc, score in results
            if score >= settings.similarity_threshold
        ]
        if not relevantes:
            return (
                "NADA RELEVANTE ENCONTRADO no material do curso para essa "
                "pergunta. Não responda por conhecimento próprio."
            )

        for doc, score in relevantes:
            sources_out.append(
                {
                    "material_id": doc.metadata.get("material_id"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "score": score,
                }
            )

        partes = [
            f"[trecho {i + 1} | relevância {score:.2f}]\n{doc.page_content}"
            for i, (doc, score) in enumerate(relevantes)
        ]
        return "\n\n".join(partes)

    @tool
    async def listar_topicos() -> str:
        """Lista os materiais do curso e sobre o que cada um trata.

        Use quando o aluno perguntar o que o curso cobre, ou quando precisar
        saber que assuntos existem antes de buscar.
        """
        async with SessionLocal() as session:
            result = await session.execute(
                select(Material).where(Material.course_id == course_id)
            )
            materiais = list(result.scalars().all())

        if not materiais:
            return "Este curso ainda não tem material cadastrado."

        linhas = []
        for m in materiais:
            inicio = (m.text or "")[:300].replace("\n", " ").strip()
            linhas.append(f"- {m.filename} ({m.media_type}): {inicio}...")
        return "\n".join(linhas)

    @tool
    async def resumir_material(nome_do_material: str = "") -> str:
        """Devolve o texto completo de um material do curso, para resumir.

        Passe o nome do arquivo. Deixe vazio para pegar o primeiro material.
        Use quando pedirem resumo ou visão geral, não para dúvidas pontuais.
        """
        async with SessionLocal() as session:
            query = select(Material).where(Material.course_id == course_id)
            if nome_do_material:
                query = query.where(Material.filename.ilike(f"%{nome_do_material}%"))
            result = await session.execute(query)
            material = result.scalars().first()

        if material is None:
            return "Material não encontrado neste curso."
        if not material.text:
            return f"O material {material.filename} ainda não foi processado."

        texto = material.text
        if len(texto) > _MAX_SUMMARY_CHARS:
            texto = texto[:_MAX_SUMMARY_CHARS] + "\n[...texto truncado...]"
        return f"Material: {material.filename}\n\n{texto}"

    @tool
    async def pedir_esclarecimento(pergunta_ao_aluno: str) -> str:
        """Pede que o aluno esclareça uma pergunta ambígua ou vaga demais.

        Use apenas quando a pergunta for genuinamente ambígua — não use para
        fugir de perguntas difíceis nem quando a busca já traz trechos úteis.
        """
        return (
            "Devolva exatamente esta pergunta ao aluno, sem acrescentar nada: "
            f"{pergunta_ao_aluno}"
        )

    return [
        buscar_no_material,
        listar_topicos,
        resumir_material,
        pedir_esclarecimento,
    ]
