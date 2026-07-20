import streamlit as st
# Asumiendo que tienes tu agente configurado en src/agent.py
from src.agent import obtener_respuesta_del_agente 

st.title("TechStore - Asistente Virtual 🤖")
st.write("¡Hola! Pregúntame sobre nuestros productos, envíos o políticas.")

# Inicializar la memoria del chat en la sesión de Streamlit
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar el historial de mensajes en la pantalla
for msg in st.session_state.mensajes:
    with st.chat_message(msg["rol"]):
        st.markdown(msg["contenido"])

# Caja de texto para que el usuario escriba
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    # Mostrar lo que escribió el usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})

    # Llamar a tu IA y mostrar la respuesta
    with st.chat_message("assistant"):
        respuesta = obtener_respuesta_del_agente(prompt) # Tu función de LangChain
        st.markdown(respuesta)
    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})