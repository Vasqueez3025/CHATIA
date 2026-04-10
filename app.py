import streamlit as st
from openai import OpenAI
import base64

# API KEY
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CONFIG
st.set_page_config(page_title="ICO IA", page_icon="🤖", layout="wide")

# ================== ESTADO ==================
if "chats" not in st.session_state:
    st.session_state.chats = {
        "Nuevo chat 1": [{"role": "system", "content": "Eres un asistente útil"}]
    }

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Nuevo chat 1"

if "chat_count" not in st.session_state:
    st.session_state.chat_count = 1

if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False

# ================== CSS ==================
st.markdown("""
<style>
body {
    background-color: #0E1117;
    color: white;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 120px;
    max-width: 900px;
}
[data-testid="stChatInput"] > div {
    background-color: #2A2B32;
    border-radius: 60px;
    border: 1px solid #3a3b42;
}
.logo-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.title("💬 Chats")

    if st.button("➕ Nuevo chat"):
        st.session_state.chat_count += 1
        new_name = f"Nuevo chat {st.session_state.chat_count}"
        st.session_state.chats[new_name] = [
            {"role": "system", "content": "Eres un asistente útil"}
        ]
        st.session_state.current_chat = new_name
        st.rerun()

    st.markdown("---")

    for chat_name in st.session_state.chats.keys():
        if st.button(chat_name):
            st.session_state.current_chat = chat_name
            st.rerun()

# ================== LOGO ==================
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
st.image("logo.png", width=800)
st.markdown('</div>', unsafe_allow_html=True)

# ================== CHAT ACTUAL ==================
messages = st.session_state.chats[st.session_state.current_chat]

# ================== MOSTRAR MENSAJES ==================
for msg in messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.markdown(item["text"])
                    elif item["type"] == "image_url":
                        st.image(item["image_url"]["url"])
            else:
                st.markdown(msg["content"])

# ================== INPUT ==================
col1, col2 = st.columns([1, 12])

with col1:
    if st.button("+"):
        st.session_state.show_uploader = not st.session_state.show_uploader

uploaded_file = None
if st.session_state.show_uploader:
    uploaded_file = st.file_uploader("Sube imagen", type=["png", "jpg", "jpeg"])

with col2:
    user_input = st.chat_input("Ask anything...")

# ================== PROCESO ==================
if user_input or uploaded_file:

    content = []

    if user_input:
        content.append({"type": "text", "text": user_input})

    if uploaded_file:
        image_bytes = uploaded_file.read()
        base64_image = base64.b64encode(image_bytes).decode()

        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    messages.append({
        "role": "user",
        "content": content if content else user_input
    })

    # 🔥 RENOMBRAR CHAT CON PRIMER MENSAJE
    if len(messages) == 2:
        new_title = user_input[:30] if user_input else "Imagen"

        original_title = new_title
        i = 1
        while new_title in st.session_state.chats:
            new_title = f"{original_title} ({i})"
            i += 1

        st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
        st.session_state.current_chat = new_title

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            reply = response.choices[0].message.content
            st.markdown(reply)

    messages.append({
        "role": "assistant",
        "content": reply
    })

# ================== LIMPIAR ==================
if st.button("🧹 Limpiar conversación"):
    st.session_state.chats[st.session_state.current_chat] = [
        {"role": "system", "content": "Eres un asistente útil"}
    ]
    st.rerun()