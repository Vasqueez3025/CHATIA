import streamlit as st
from openai import OpenAI

# 🔐 API KEY SEGURA (NO EN EL CÓDIGO)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="ICO UNIFORMS 4.0", page_icon="🤖")
st.title("🤖 ICO IA")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Eres un asistente útil"}
    ]

# Mostrar historial
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input usuario
user_input = st.chat_input("Escribe tu mensaje...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )

            reply = response.choices[0].message.content
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# Botón limpiar chat
if st.button("🧹 Limpiar conversación"):
    st.session_state.messages = [
        {"role": "system", "content": "Eres un asistente útil"}
    ]
    st.rerun()