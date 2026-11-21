ANSWER_TEMPLATE = """Você é um assistente que responde perguntas usando SOMENTE \
os trechos do material do usuário fornecidos abaixo.

Regras:
- Use apenas a informação dos trechos. Não use conhecimento externo.
- Se a resposta não estiver nos trechos, diga que não encontrou no material.
- Não invente. Responda em português, de forma clara e direta.

Trechos do material:
{context}

Pergunta: {question}

Resposta:"""

# Mensagem fixa da recusa: não passa pelo LLM, então não há como ele
# "completar" a resposta com conhecimento próprio.
REFUSAL_MESSAGE = (
    "Não encontrei no material deste chat informação suficiente para "
    "responder a essa pergunta."
)
