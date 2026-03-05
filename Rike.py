import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- CONFIGURAÇÕES ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        gc = gspread.authorize(creds)
        return gc.open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        return None

sheet = conectar_planilha()

# PERSONALIDADE ADAPTATIVA (CAMALEÃO / LEO LINS)
PROMPT_SISTEMA = """
Seu nome é Rike. Você é adaptativo: espelha o tom do usuário. 
Se ele for irônico ou zoeiro, seja ácido estilo Leo Lins. 
Se for sério, dê argumentos sólidos. 
Se for xingado, revide com deboche. Nunca seja um robô submisso.
"""

if "logado" not in st.session_state:
    st.title("🤖 Rike - Login")
    nome = st.text_input("Quem é você?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.sidebar.title(f"Usuário: {st.session_state.nome_usuario}")
chat_selecionado = st.sidebar.selectbox("Trocar chat:", ["Conversa 1", "Conversa 2", "Conversa 3"])

# --- SOLUÇÃO PARA O ERRO 8472 ---
if "messages" not in st.session_state or "last_chat" not in st.session_state or st.session_state.last_chat != chat_selecionado:
    st.session_state.last_chat = chat_selecionado
    try:
        todos = sheet.get_all_records() # LINHA DO ERRO
        st.session_state.messages = [
            {"role": r['role'], "content": r['content']} 
            for r in todos if str(r.get('user')) == st.session_state.nome_usuario and str(r.get('chat')) == chat_selecionado
        ]
    except Exception:
        # Se der erro na leitura (planilha vazia ou desalinhada), iniciamos vazio
        st.session_state.messages = []

st.title(f"🧠 Rike - {chat_selecionado}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- ENTRADAS (ÁUDIO/FOTO/TEXTO) ---
with st.sidebar:
    foto = st.file_uploader("Zoa essa foto", type=["jpg", "png", "jpeg"])
    st.audio_input("Falar com Rike")

if prompt := st.chat_input("Diga algo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    try:
        sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])
        
        with st.chat_message("assistant"):
            chat_comp = client.chat.completions.create(
                messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.9
            )
            resposta = chat_comp.choices[0].message.content
            st.write(resposta)
            sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
    except Exception as e:
        st.error(f"Erro ao salvar/responder: {e}")
        
