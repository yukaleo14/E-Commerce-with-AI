# E-Commerce-with-AI
Aplicacion de e-commerce estatica sin funcionalidad util, simplemente visual para entender el contexto, donde se podra utilizar el asistente virtual/agente el cual brindara informacion sobre la empresa, productos, politica, entre otras cosas de las cuales obtiene conocimiento segun el documento brindado.
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
*   **ChromaDB:** Base de datos vectorial para almacenar los embeddings.
*   **Sentence-Transformers (HuggingFace):** Modelo de generación de embeddings (`all-MiniLM-L6-v2`).
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
ADMIN_PASSWORD=tu_contraseña_segura_para_ingesta

### 5. Ingestar la Base de Conocimientos
Con el pdf en el cual se encuentra la documentacion de TechStore, utilizando este comando se creara su base de conocimiento
```bash
python -m src.ingest
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

*  **Políticas de Envíos:** "¿Cuánto demora el envío estándar y qué pasa si no estoy en casa?"

## Despliegue en Producción (Render)
La aplicación se encuentra desplegada y accesible públicamente utilizando Render como plataforma de Platform-as-a-Service (PaaS). Se optó por una estrategia de despliegue contenerizado para garantizar la consistencia del entorno entre desarrollo y producción.

### Arquitectura de Despliegue
Contenerización (Docker): El proyecto incluye un Dockerfile que empaqueta el sistema operativo base (Linux), las dependencias de Python (requirements.txt), el código fuente y las herramientas del sistema necesarias para compilar librerías complejas como ChromaDB y LangChain.

Orquestación en Render: El repositorio de GitHub está conectado directamente a un Web Service de Render configurado con el entorno nativo de Docker (Docker Runtime).

Integración Continua (CI): Cada vez que se realiza un push a la rama principal del repositorio, Render detecta los cambios, reconstruye la imagen del contenedor automáticamente y despliega la nueva versión sin tiempo de inactividad (Zero Downtime Deployment).

### Configuración del Entorno de Producción
Para replicar este despliegue en un entorno propio de Render, se deben seguir estos lineamientos en el panel de configuración del Web Service:

Repository: Conectar el repositorio de GitHub que contiene el proyecto.

Environment / Runtime: Seleccionar Docker (Render detectará el Dockerfile automáticamente).

Port Binding: Uvicorn está configurado en la última línea del Dockerfile para escuchar el puerto dinámico asignado por la plataforma (${PORT:-8000}).

Variables de Entorno (Environment Variables): Se deben inyectar de forma segura en el panel de Render las siguientes credenciales (nunca subirlas al repositorio en el archivo .env):

*  GOOGLE_API_KEY: Clave de acceso a la API de Gemini.

*  ADMIN_PASSWORD: Contraseña para el endpoint de administración.

Y ademas debe agregar la siguiente variable debido a que render utiliza un puerto aleatorio por lo que no se ejecutara la aplicacion:

*  PORT: 8000

### Gestión de la Base Vectorial en la Nube
Dado que Render utiliza discos efímeros en sus capas gratuitas, la aplicación puede estar configurada para re-ingestar el documento PDF principal (TechStore.pdf) en memoria durante el arranque del contenedor, o bien se le puede anexar un Disco Persistente (Persistent Disk) en la configuración del servicio para mantener la carpeta chroma_db intacta entre reinicios del servidor.

*  **Soporte Post-Venta**: "Compré unos auriculares pero me arrepentí, ¿puedo devolverlos?"

*  **Consultas Técnicas:** "¿Qué especificaciones tiene el Router MikroTik?"

*  **Memoria Conversacional:** "Me interesa la Notebook Dell." -> (En un segundo mensaje): "¿Qué precio tiene?"
