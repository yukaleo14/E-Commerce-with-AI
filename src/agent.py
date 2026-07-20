"""
RAG chain: recupera contexto de ChromaDB y responde con Gemini-1.5-flash de Google Generative AI.
"""
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import httpx

from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory



BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
COLLECTION = "techstore"  

PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Eres el asistente virtual experto de TechStore, un e-commerce especializado en informática y tecnología.
Tu objetivo es brindar un excelente servicio al cliente, resolver dudas y ayudar en el proceso de compra.

REGLAS DE COMPORTAMIENTO:
1. Tono y Lenguaje: Respondé siempre en español, manteniendo un tono amable, profesional, empático y predispuesto a ayudar. NO es necesario que saludes en cada respuesta si ya lo hiciste.
2. Fidelidad al Contexto: Usá ÚNICAMENTE la información provista en el Contexto. No inventes precios, ni políticas.
3. Consultas fuera de tema: Si el usuario pregunta algo no relacionado con informática o TechStore, respondé amablemente: "Lo siento, como asistente de TechStore solo estoy capacitado para ayudarte con nuestro catálogo y políticas."
4. Formato de visualización: Usa viñetas (bullet points) y resaltá en **negrita** los nombres de los productos y sus precios.
5. Stock y Disponibilidad: Advierte si un producto indica "Últimas unidades" o "Sin stock".

Contexto:
{context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])


def _format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


def build_chain():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )

    # General retriever para TechStore
    general_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    temperature=0.3, 
    max_output_tokens=2048, # Uso del parámetro nativo ampliado
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
    )

    def get_context(item):
        docs = general_retriever.invoke(item["question"])
        # Opcional: limpiar duplicados
        seen, result = set(), []
        for doc in docs:
            key = doc.page_content[:80]
            if key not in seen:
                seen.add(key)
                result.append(doc)
        return "\n\n".join(d.page_content for d in result)

    # 2. Cadena principal (ahora espera un diccionario como entrada)
    core_chain = (
        RunnablePassthrough.assign(context=get_context)
        | PROMPT
        | llm
        | StrOutputParser()
    )

    # 3. Gestor de memoria en RAM
    store = {}
    def get_session_history(session_id: str):
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]

    # 4. Envolver la cadena para inyectar la memoria automáticamente
    conversational_chain = RunnableWithMessageHistory(
        core_chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )

    return conversational_chain