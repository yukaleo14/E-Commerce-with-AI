import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Cargar las variables de entorno
load_dotenv()

def realizar_ingesta(ruta_pdf: str):
    print(f"📄 Cargando el archivo: {ruta_pdf}...")
    loader = PyMuPDFLoader(ruta_pdf)
    documentos = loader.load()

    print("✂️ Dividiendo el texto en fragmentos...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(documentos)
    print(f"✅ Se generaron {len(chunks)} fragmentos.")

    print("☁️ Subiendo vectores a Pinecone (esto puede tardar un momento)...")
    
    # Configuramos el mismo modelo de embeddings que usa tu agente
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    
    # Subimos los documentos al índice existente
    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name="e-commerce-ai"
    )
    
    print("🚀 ¡Ingesta completada con éxito! La base de datos está lista.")

if __name__ == "__main__":
    # Reemplaza esto con la ruta real de tu catálogo PDF de TechStore
    RUTA_AL_PDF = "../TechStore.pdf" 
    
    if os.path.exists(RUTA_AL_PDF):
        realizar_ingesta(RUTA_AL_PDF)
    else:
        print("❌ Error: No se encontró el archivo PDF en la ruta especificada.")