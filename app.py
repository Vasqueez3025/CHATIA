import streamlit as st
from openai import OpenAI
import base64
from PyPDF2 import PdfReader
from datetime import datetime
import requests

# ================== CONFIG ==================
st.set_page_config(page_title="JV IA PRO", page_icon="🤖", layout="wide")

# 🔐 API KEY
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================== GEO ==================
@st.cache_data(ttl=300)
def obtener_geo():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        d = r.json()
        return {
            "ciudad": d.get("city", ""),
            "pais": d.get("country_name", ""),
            "lat": d.get("latitude", None),
            "lon": d.get("longitude", None)
        }
    except:
        return {"ciudad": "", "pais": "", "lat": None, "lon": None}

geo = obtener_geo()
ubicacion = f"{geo['ciudad']}, {geo['pais']}"
hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ================== CLIMA REAL ==================
@st.cache_data(ttl=600)
def obtener_clima(lat, lon):
    try:
        if lat is None or lon is None:
            return None
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        r = requests.get(url, timeout=5)
        data = r.json()
        w = data.get("current_weather", {})
        return {
            "temp": w.get("temperature"),
            "wind": w.get("windspeed")
        }
    except:
        return None

clima = obtener_clima(geo["lat"], geo["lon"])

# ================== ESTADO ==================
if "chats" not in st.session_state:
    st.session_state.chats = {
        "Nuevo chat": [{"role": "system", "content": "Eres un asistente útil"}]
    }

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Nuevo chat"

if "style" not in st.session_state:
    st.session_state.style = "Realista"

# ================== CSS ==================
st.markdown("""
<style>
.stApp {background-color: #0f172a; color: white;}
header {visibility: hidden;}

#header-fixed {
    position: fixed;
    top: 0;
    left: 300px;
    right: 0;
    height: 60px;
    background: rgba(2,6,23,0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #1e293b;
    display: flex;
    align-items: center;
    padding-left: 20px;
    z-index: 999;
}

.chat-bubble-user {
    background: #1e293b;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 8px;
}

.chat-bubble-assistant {
    background: #020617;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 8px;
    border: 1px solid #1e293b;
}

.stChatInput {
    position: fixed;
    bottom: 20px;
    left: 300px;
    right: 40px;
}

section[data-testid="stSidebar"] {
    background-color: #020617;
    border-right: 1px solid #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ================== HEADER ==================
clima_txt = ""
if clima:
    clima_txt = f"🌡️ {clima['temp']}°C"

st.markdown(f"""
<div id="header-fixed">
    <h3>🤖 JV IA PRO</h3>
    <div style="margin-left:auto; margin-right:20px; font-size:12px; opacity:0.7;">
        📍 {ubicacion} | 🕒 {hora_actual} {clima_txt}
    </div>
</div>
""", unsafe_allow_html=True)

# ================== FUNCIONES ==================
def decidir_tipo_respuesta(user_input):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Responde SOLO con 'imagen' o 'texto'."},
            {"role": "user", "content": user_input}
        ],
        max_tokens=5
    )
    return r.choices[0].message.content.strip().lower()

def aplicar_estilo(prompt):
    estilos = {
        "Realista": "ultra realista, fotografía profesional, 4k",
        "Anime": "anime japonés",
        "3D": "render 3D cinematográfico",
        "Pixel Art": "pixel art retro",
        "Dibujo": "ilustración artística"
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
    st.image("logo.png", width=140)

    if st.button("➕ Nuevo chat"):
        name = f"Chat {len(st.session_state.chats)+1}"
        st.session_state.chats[name] = [{"role": "system", "content": "Eres un asistente útil"}]
        st.session_state.current_chat = name
        st.rerun()

    st.markdown("---")

    for c in st.session_state.chats:
        if st.button(c):
            st.session_state.current_chat = c
            st.rerun()

    st.markdown("---")

    st.selectbox("🎨 Estilo",
        ["Realista", "Anime", "3D", "Pixel Art", "Dibujo"],
        key="style"
    )

    st.markdown("---")

    file = st.file_uploader("📄 Subir PDF", type=["pdf"])
    if file:
        contenido_pdf = leer_pdf(file)
        st.session_state.chats[st.session_state.current_chat].append({
            "role": "system",
            "content": f"Contenido del PDF:\n{contenido_pdf}"
        })
        st.success("PDF cargado")

    if st.button("🧹 Limpiar chat"):
        st.session_state.chats[st.session_state.current_chat] = [
            {"role": "system", "content": "Eres un asistente útil"}
        ]
        st.rerun()

# ================== CHAT ==================
messages = st.session_state.chats[st.session_state.current_chat]

for msg in messages:
    if msg["role"] != "system":
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            if "data:image" in str(msg["content"]):
                st.image(msg["content"])
            else:
                st.markdown(f'<div class="chat-bubble-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

# ================== INPUT ==================
user_input = st.chat_input("Escribe como ChatGPT...")

# ================== PROCESO ==================
if user_input:

    # Mostrar instantáneo
    st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)

    messages.append({"role": "user", "content": user_input})

    contexto = f"""
Ubicación: {ubicacion}
Hora: {hora_actual}
Clima: {clima}
"""

    with st.spinner("Pensando..."):

        tipo = decidir_tipo_respuesta(user_input)

        # ================== IMAGEN ==================
        if tipo == "imagen":
            prompt_final = aplicar_estilo(user_input)

            img = client.images.generate(
                model="gpt-image-1",
                prompt=prompt_final,
                size="1024x1024"
            )

            image_base64 = img.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            st.image(image_bytes)

            messages.append({
                "role": "assistant",
                "content": f"data:image/jpeg;base64,{image_base64}"
            })

        # ================== TEXTO STREAM ==================
        else:
            container = st.empty()
            full = ""

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": contexto},
                    *messages
                ],
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full += token

                    container.markdown(
                        f'<div class="chat-bubble-assistant">{full}▌</div>',
                        unsafe_allow_html=True
                    )

            container.markdown(
                f'<div class="chat-bubble-assistant">{full}</div>',
                unsafe_allow_html=True
            )

            messages.append({
                "role": "assistant",
                "content": full
            })