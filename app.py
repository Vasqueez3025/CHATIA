import streamlit as st
from openai import OpenAI
import base64
from PyPDF2 import PdfReader

# 🔐 API KEY
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="ICO IA PRO", page_icon="🤖", layout="wide")

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

if "style" not in st.session_state:
    st.session_state.style = "Realista"

# ================== FUNCIONES ==================

def decidir_tipo_respuesta(user_input):
    decision = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Responde SOLO con 'imagen' o 'texto'."},
            {"role": "user", "content": user_input}
        ],
        max_tokens=5
    )
    return decision.choices[0].message.content.strip().lower()

def aplicar_estilo(prompt):
    estilos = {
        "Realista": "ultra realista, fotografía profesional, 4k",
        "Anime": "anime estilo japonés, tipo studio ghibli",
        "3D": "render 3D, iluminación cinematográfica",
        "Pixel Art": "pixel art retro",
        "Dibujo": "ilustración artística detallada"
    }
    return f"{estilos.get(st.session_state.style, '')}: {prompt}"

def leer_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:4000]

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

    st.markdown("---")

    st.selectbox("🎨 Estilo de imagen",
                 ["Realista", "Anime", "3D", "Pixel Art", "Dibujo"],
                 key="style")

# ================== LOGO ==================
st.image("logo.png", width=600)

# ================== CHAT ==================
messages = st.session_state.chats[st.session_state.current_chat]

for msg in messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.markdown(item["text"])

                    elif item["type"] == "image_url":
                        try:
                            img = item.get("image_url", {}).get("url")
                            if img:
                                st.image(img)
                        except:
                            st.warning("Error cargando imagen")
            else:
                st.markdown(msg["content"])

# ================== INPUT ==================
col1, col2 = st.columns([1, 12])

with col1:
    if st.button("+"):
        st.session_state.show_uploader = not st.session_state.show_uploader

uploaded_file = None
pdf_text = ""

if st.session_state.show_uploader:
    uploaded_file = st.file_uploader("Sube imagen o PDF", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file and uploaded_file.type == "application/pdf":
        pdf_text = leer_pdf(uploaded_file)

with col2:
    user_input = st.chat_input("Escribe aquí...")

# ================== PROCESO ==================
if user_input or uploaded_file:

    content = []

    if user_input:
        content.append({"type": "text", "text": user_input})

    if pdf_text:
        content.append({"type": "text", "text": f"Contenido del PDF:\n{pdf_text}"})

    if uploaded_file and uploaded_file.type != "application/pdf":
        image_bytes = uploaded_file.read()
        base64_image = base64.b64encode(image_bytes).decode()

        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    messages.append({"role": "user", "content": content})

    # RENOMBRAR CHAT
    if len(messages) == 2 and user_input:
        new_title = user_input[:30]
        st.session_state.chats[new_title] = st.session_state.chats.pop(st.session_state.current_chat)
        st.session_state.current_chat = new_title

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):

            tipo = decidir_tipo_respuesta(user_input or "")

            if tipo == "imagen":

                prompt_final = aplicar_estilo(user_input)

                img = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt_final,
                    size="1024x1024"
                )

                # 🔥 FIX BASE64
                image_base64 = img.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)

                st.image(image_bytes)

                messages.append({
                    "role": "assistant",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                })

            else:
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