from contextlib import asynccontextmanager
import os
from pathlib import Path
import shutil
import tempfile
from dotenv import load_dotenv
import uvicorn

load_dotenv()

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.agent import build_chain
from src.ingest_add import ingest_add

STATIC_DIR = Path(__file__).resolve().parent / "static"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
chain = None



@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    chain = build_chain()
    yield


app = FastAPI(title="TechStore AI Agent", lifespan=lifespan)


class Question(BaseModel):
    question: str
    session_id: str = "default_session"


class Answer(BaseModel):
    answer: str


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
def admin():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check-auth")
def check_auth(x_admin_password: str | None = Header(default=None)):
    if not ADMIN_PASSWORD or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="No autorizado.")
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...), x_admin_password: str | None = Header(default=None)):
    if not ADMIN_PASSWORD or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="No autorizado.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        result = ingest_add(tmp_path, original_name=file.filename)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@app.post("/ask", response_model=Answer)
def ask(body: Question):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")
    
    try:
        # Intentamos obtener la respuesta de Gemini
        result = chain.invoke(
            {"question": body.question},
            config={"configurable": {"session_id": body.session_id}}
        )
        return Answer(answer=result)
        
    except Exception as e:
        # Capturamos cualquier error que arroje LangChain o la API
        error_str = str(e)

        print(f"🔥 ERROR INTERNO: {error_str}", flush=True)
        
        # Verificamos si el error es por límite de cuota (429)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            mensaje_espera = (
                "¡Uy! Hay muchos clientes consultando al mismo tiempo y mi sistema está un poco saturado. "
                "Por favor, **espera aproximadamente un minuto** y vuelve a enviarme tu pregunta. ¡Gracias por la paciencia!"
            )
            return Answer(answer=mensaje_espera)
        
        # Fallback para cualquier otro tipo de error técnico (como pérdida de conexión)
        return Answer(answer="Lo siento, tuve un problema técnico momentáneo al procesar tu consulta. ¿Podrías intentar de nuevo?")
    

if __name__ == "__main__":
    # Lee el puerto de Render o usa 8000 por defecto
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port)