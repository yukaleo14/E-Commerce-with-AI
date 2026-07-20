import streamlit as st
from src.agent import build_chain

st.title("TechStore - Asistente Virtual 🤖")

# 1. Cargamos el agente en caché para que solo se construya una vez
@st.cache_resource
def iniciar_agente():
    return build_chain()

# Instanciamos el agente
agente = iniciar_agente()

# 2. Inicializamos el historial visual en Streamlit
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for msg in st.session_state.mensajes:
    with st.chat_message(msg["rol"]):
        st.markdown(msg["contenido"])

# 3. Lógica del Chat
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})

    with st.chat_message("assistant"):
        # Llamamos al agente de LangChain
        # Pasamos el input_messages_key y el session_id que configuraste
        respuesta_cruda = agente.invoke(
            {"question": prompt},
            config={"configurable": {"session_id": "sesion_streamlit_unica"}}
        )
        
        # Como usaste StrOutputParser() en tu core_chain, 
        # la respuesta ya es el texto directo, no un diccionario.
        respuesta_final = respuesta_cruda
        
        st.markdown(respuesta_final)
        
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_final})