"""
Agrega un PDF nuevo a la colección ChromaDB existente sin borrar lo que ya está.
Uso CLI: python -m app.ingest_add ruta/al/archivo.pdf
Uso API: from app.ingest_add import ingest_add
"""
import os
import ssl
import sys

ssl._create_default_https_context = ssl._create_unverified_context
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import httpx
_orig_client_init = httpx.Client.__init__
def _no_verify_client_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _orig_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _no_verify_client_init

from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = str(BASE_DIR / "data" / "chroma_db")
COLLECTION = "techstore"  


def ingest_add(pdf_path: str, original_name: str | None = None) -> dict:
    """
    Indexa un PDF en la colección existente.
    original_name: nombre original del archivo (para deduplicación cuando pdf_path es un archivo temporal).
    Retorna dict con status, mensaje, chunks_added y total.
    """
    path = Path(pdf_path).resolve()
    display_name = original_name or path.name

    if not path.exists():
        return {"status": "error", "message": f"Archivo no encontrado: {path}", "chunks_added": 0, "total": 0}
    if not display_name.lower().endswith(".pdf"):
        return {"status": "error", "message": f"El archivo debe ser un PDF: {display_name}", "chunks_added": 0, "total": 0}

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION,
    )

    existing = vectorstore.get(include=["metadatas"])
    # Comparar por nombre de archivo, no por path completo
    indexed_names = {Path(m.get("source", "")).name for m in existing["metadatas"]}
    total = len(existing["ids"])

    if display_name in indexed_names:
        return {
            "status": "already_indexed",
            "message": f"{display_name} ya está indexado.",
            "chunks_added": 0,
            "total": total,
        }

    loader = PyMuPDFLoader(str(path))
    docs = loader.load()

    # Normalizar source al nombre original para que la deduplicación futura funcione
    for doc in docs:
        doc.metadata["source"] = display_name

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    if not chunks:
        return {
            "status": "error",
            "message": "El PDF no tiene texto extraíble (puede ser una imagen escaneada).",
            "chunks_added": 0,
            "total": total,
        }

    vectorstore.add_documents(chunks)
    total_new = len(vectorstore.get()["ids"])

    return {
        "status": "added",
        "message": f"{display_name} indexado correctamente.",
        "chunks_added": len(chunks),
        "total": total_new,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m app.ingest_add ruta/al/archivo.pdf")
        sys.exit(1)
    result = ingest_add(sys.argv[1])
    print(result["message"])
    if result["status"] != "error":
        print(f"Chunks agregados: {result['chunks_added']} | Total en colección: {result['total']}")
    sys.exit(0 if result["status"] != "error" else 1)