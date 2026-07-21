# E-Commerce-with-AI
Aplicacion de e-commerce estatica sin funcionalidad util, simplemente visual para entender el contexto, donde se podra utilizar el asistente virtual/agente el cual brindara informacion sobre la empresa, productos, politica, entre otras cosas de las cuales obtiene conocimiento segun el documento brindado.

<img width="1600" height="741" alt="imagen home" src="https://github.com/user-attachments/assets/49d0b44e-e152-47c3-9ce7-dcf9d933cbe0" />

# TechStore - E-commerce con Asistente Virtual RAG (Gemini)
## Descripción General
TechStore es una plataforma web estática orientada al comercio electrónico de componentes informáticos, periféricos y equipos tecnológicos. El principal valor agregado de este proyecto es la integración de un **agente de inteligencia artificial conversacional** directamente en la interfaz de usuario.

Esta aplicación funciona como una prueba de concepto (PoC) que demuestra cómo automatizar el soporte de primer nivel y mejorar la retención de usuarios. A través de un widget de chat integrado, el asistente resuelve dudas sobre políticas de empresa, envíos, devoluciones, precios y características del catálogo de productos en tiempo real, sin intervención humana.

---

## Arquitectura de la Solución
El proyecto está construido bajo una arquitectura cliente-servidor con un motor RAG (Generación Aumentada por Recuperación) para dotar de contexto a la inteligencia artificial.

1.  **Frontend (Cliente):** Interfaz estática (HTML/CSS/JS) con diseño responsivo. Cuenta con un catálogo de productos visual y un widget de chat asíncrono que se comunica con el backend mediante peticiones `fetch`.
2.  **Backend (Servidor Web):** Desarrollado en Python, expone endpoints RESTful para la carga de documentos (`/upload`) y la interacción con el chat (`/ask`).
3.  **Motor RAG y Base Vectorial:** El sistema ingesta documentación estandarizada en formato PDF, la divide en fragmentos semánticos y la almacena en una base de datos vectorial local.
4.  **Agente Conversacional:** Orquestado con cadenas (chains), el agente recupera el contexto relevante de la base de datos según la pregunta del usuario y utiliza un LLM para formular una respuesta natural, manteniendo un registro temporal de la memoria de la conversación (Session History). Se incluye un manejador de excepciones para administrar gracefully los límites de cuota (Rate Limits) de la API.

---

## Tecnologías y Herramientas Utilizadas

**Frontend:**
*   HTML5
*   CSS3 (Flexbox/Grid, Variables)
*   Vanilla JavaScript

**Backend & IA:**
*   **Python 3.12+**
*   **FastAPI / Uvicorn:** Framework para la creación de la API y servidor ASGI.
*   **LangChain:** Framework de orquestación de IA y manejo de memoria (`RunnableWithMessageHistory`).
*   **Google Gemini (gemini-1.5-flash-001):** Modelo de Lenguaje Grande (LLM) principal.
*   **Google Embeddings (text-embedding-004):** Modelo de generación de vectores.
*   **Pinecone:** Base de datos vectorial administrada en la nube (Serverless Vector Database).
*   **PyMuPDFLoader:** Extracción y lectura nativa de archivos PDF.

---

## Instrucciones para Ejecutar el Proyecto

Sigue estos pasos para levantar el entorno localmente:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tu-usuario/techstore-ai-agent.git](https://github.com/tu-usuario/techstore-ai-agent.git)
cd techstore-ai-agent
```
### 2. Instalar las dependencias
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
En tu archivo **.env** agrega las siguientes variables
GOOGLE_API_KEY=tu_clave_de_google_ai_studio_aqui
PINECONE_API_KEY="tu_clave_de_pinecone"
ADMIN_PASSWORD=tu_contraseña_segura_para_ingesta

### 5. Ingestar la Base de Conocimientos
Con el pdf en el cual se encuentra la documentacion de TechStore, utilizando este comando se creara su base de conocimiento
Y para evitar sobrecargar el servidor web, la ingesta del documento PDF se realiza de forma local. Ejecuta el script de ingesta para procesar el catálogo y enviar los vectores a tu índice de Pinecone en la nube:
```bash
python ingest_pinecone.py
```

### 6. Levantar el Servidor
```bash
uvicorn src.main:app --reload
```
*  La aplicación estará disponible en: http://localhost:8000

*  El panel de administración para subir nuevos PDFs estará en: http://localhost:8000/admin

#### Ejemplos de Interaccion
Ejemplos de preguntas que el agente puede responder:
*  **Stock y Catálogo:** "¿Tienen monitores curvos disponibles y cuál es su precio?"
<img width="417" height="568" alt="img preg monitores" src="https://github.com/user-attachments/assets/a53d6d29-e240-4fe6-a268-ec2c663ba276" />


* **Sobrecarga del modelo gratuito:** Al tratarse del modelo gratuito de gemini, el agente podra realizar respuestas limitadas segun la cantidad de tokens consumidos, por lo que en caso de que se pase ese limite, el agente respondera con un mensaje aclarando esa situacion al cliente
<img width="420" height="557" alt="limitacion modelo " src="https://github.com/user-attachments/assets/5620b1aa-34f4-4b46-86e3-e4e15b0efc9e" />

## Despliegue en Producción (Render + Pinecone)

La aplicación se encuentra desplegada utilizando **Render** (como plataforma PaaS para el servidor web) y **Pinecone** (como base de datos vectorial en la nube).

### ¿Por qué esta arquitectura? (Resolución de OOM)
Durante el desarrollo, la base de datos se almacenaba localmente usando ChromaDB y los embeddings se generaban con modelos de HuggingFace (`sentence-transformers` / `PyTorch`). Sin embargo, el plan gratuito de Render impone un límite estricto de **512 MB de memoria RAM**. Cargar librerías de Deep Learning y procesar el documento en memoria durante el arranque del servidor provocaba errores de `Out of memory (OOM)`.

**La Solución:** Se aplicó el principio de **desacoplamiento**. 
1. Se delegó el almacenamiento vectorial a **Pinecone**.
2. Se delegó la creación de embeddings a la API de **Google** (`text-embedding-004`).
3. Se eliminó la ingesta del PDF del ciclo de vida del servidor web (`main.py`).

De esta manera, el contenedor Docker en Render es ultraligero (consume menos de 150 MB de RAM). FastAPI simplemente actúa como un puente: recibe la consulta del HTML, busca en Pinecone, le pasa el contexto a Gemini y devuelve la respuesta.

### Configuración en Pinecone
Para que la base de datos sea compatible con los embeddings de Google, el índice en Pinecone debe configurarse con los siguientes parámetros exactos:
*   **Index Name:** `e-commerce-ai`
*   **Dimensions:** `3072`
*   **Metric:** `cosine`

### Configuración en Render
Para replicar este despliegue en Render, se debe configurar un nuevo *Web Service* utilizando **Docker** como entorno nativo.[cite: 6]

En la pestaña *Environment*, es obligatorio declarar las siguientes variables para que el contenedor pueda enlazar los servicios:
*   `GOOGLE_API_KEY`: Clave de acceso a la API de Gemini.
*   `PINECONE_API_KEY`: Credencial de conexión a la base de datos.
*   `PORT`: `8000` (Para coincidir con la exposición del Dockerfile).
