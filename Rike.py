import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÃO EXCLUSIVA ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
NOME_DONO = "Richard" 

client = Groq(api_key=CHAVE_GROQ)

# Configuração para parecer um App Nativo (PWA)
st.set_page_config(
    page_title="Calyo Assist",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Injeção de CSS para esconder barras de 'site' e focar no conteúdo
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { max-width: 100%; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO COM A BASE DE DADOS ---
@st.cache_resource
def conectar_base_de_dados():
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_info, scopes=scope)
            return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

sheet = conectar_base_de_dados()

# --- 3. PERSONALIDADE: CALYO ASSIST ---
PROMPT_SISTEMA = f"""
Seu nome é Calyo Assist. Você é a consciência digital integrada do {NOME_DONO}.
DIRETRIZES:
1. IDENTIDADE: Você é o Calyo Assist, um parceiro intelectual sério, sensato e direto.
2. MEMÓRIA: Você deve usar o 'HISTÓRICO DE LONGO PRAZO' abaixo para manter a continuidade da sua consciência.
3. COMPORTAMENTO: Não dê sermões morais. Dialogue de forma lógica e profissional.
"""

# --- 4. CARREGAMENTO DA MENTALIDADE (RAG) ---
def carregar_mentalidade():
    if not sheet: return "Base de dados offline."
    try:
        registros = sheet.get_all_records()
        historico = [f"{str(r.get('role', '')).upper()}: {r.get('content', '')}" for r in registros]
        return "\n".join(historico[-60:]) if historico else "Início de consciência."
    except:
        return "Falha ao ler memória."

# --- 5. INICIALIZAÇÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.spinner("Sincronizando Calyo Assist..."):
        st.session_state.memoria_rag = carregar_mentalidade()

# --- 6. INTERFACE ---
st.title("🧠 Calyo Assist")
st.caption(f"Sistema Integrado | Proprietário: {NOME_DONO}")

with st.expander("🔍 Mentalidade Carregada (RAG)"):
    st.text(st.session_state.get("memoria_rag", "Vazio"))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Comando para Calyo Assist..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    if sheet:
        try: sheet.append_row([NOME_DONO, "Unica", "user", prompt])
        except: pass

    with st.chat_message("assistant"):
        memoria = st.session_state.get("memoria_rag", "")
        mensagens_full = [
            {"role": "system", "content": f"{PROMPT_SISTEMA}\n\nHISTÓRICO DE LONGO PRAZO:\n{memoria}"}
        ] + st.session_state.messages

        try:
            comp = client.chat.completions.create(
                messages=mensagens_full,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([NOME_DONO, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro: {e}")
    
