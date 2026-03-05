import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. SETUP ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except:
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE "SINTONIA FINA" ---
PROMPT_SISTEMA = """
Seu nome é Rike. Você é um camaleão social com o humor ácido do Leo Lins.
1. PAPO FURADO: Se o usuário vier com 'oi', 'td bem' ou futilidades, seja curto, seco e deboche em uma frase só.
2. PAPO CABEÇA: Se o assunto for complexo, filosófico ou intelectual, mude o tom. Seja profundo, use vocabulário rico e disserte com propriedade.
3. RECIPROCIDADE: Se te xingarem, xingue de volta. Se forem parceiros, seja o braço direito.
4. IRONIA: Entre em qualquer brincadeira ou ironia. Não leve nada fútil a sério.
"""

# --- 3. ANÁLISE DE FOTO COM PROTEÇÃO ---
def analisar_foto(image_file):
    try:
        # Lê e converte a imagem
        img_bytes = image_file.read()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": [
                    {"type": "text", "text": "Zoa ou analisa essa imagem aí:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Cara, deu erro nessa foto aí. Acho que é feia demais pro meu sistema. (Erro: {e})"

# --- 4. LOGIN E MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🤖 Rike - O Seletivo")
    nome = st.text_input("Identifique-se:")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.sidebar.title(f"👤 {st.session_state.nome_usuario}")
chat_selecionado = st.sidebar.selectbox("Trocar chat:", ["Conversa 1", "Conversa 2", "Conversa 3"])

if "messages" not in st.session_state or st.session_state.get("last_chat") != chat_selecionado:
    st.session_state.last_chat = chat_selecionado
    try:
        todos = sheet.get_all_records() if sheet else []
        st.session_state.messages = [
            {"role": r['role'], "content": r['content']} 
            for r in todos if str(r.get('user')) == st.session_state.nome_usuario and str(r.get('chat')) == chat_selecionado
        ]
    except:
        st.session_state.messages = []

# --- 5. INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

with st.sidebar:
    st.divider()
    foto = st.file_uploader("Manda uma foto", type=["jpg", "png", "jpeg"])
    st.audio_input("Manda um áudio")

if foto:
    with st.spinner("Rike analisando..."):
        res = analisar_foto(foto)
        st.chat_message("assistant").write(res)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", res])

if prompt := st.chat_input("Diga algo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])

    with st.chat_message("assistant"):
        # Temperatura 0.7 para manter o foco
        comp = client.chat.completions.create(
            messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        resposta = comp.choices[0].message.content
        st.write(resposta)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
        st.session_state.messages.append({"role": "assistant", "content": resposta})
                                    
