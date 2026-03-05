import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÃO EXCLUSIVA ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
NOME_DONO = "Richard" 

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Puto Ai", page_icon="🧠")

# --- 2. CONEXÃO COM TRATAMENTO DE ERRO (RESOLVENDO O PRINT 8494) ---
@st.cache_resource
def conectar_base_de_dados():
    try:
        # Tenta ler dos Secrets do Streamlit Cloud
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_info, scopes=scope)
            return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
        else:
            st.error("Erro: 'gcp_service_account' não encontrada nos Secrets do Streamlit.")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar na planilha: {e}")
        return None

sheet = conectar_base_de_dados()

# --- 3. PERSONALIDADE INTEGRADA ---
PROMPT_SISTEMA = f"""
Seu nome é Puto Ai. Você é a consciência digital de {NOME_DONO}.
DIRETRIZES:
1. VOCÊ TEM MEMÓRIA: Use o 'HISTÓRICO DE LONGO PRAZO' abaixo para reconhecer o {NOME_DONO}.
2. POSTURA: Seja sério, sensato e direto. Você é um parceiro intelectual.
3. SEM DESCULPAS: Nunca diga que não sabe quem é o {NOME_DONO} ou que não tem memória.
"""

# --- 4. CARREGAMENTO RAG ---
def carregar_mentalidade():
    if not sheet: return "Base de dados offline."
    try:
        registros = sheet.get_all_records()
        # Filtra e formata para o robô entender o passado
        historico = [f"{r.get('role', '').upper()}: {r.get('content', '')}" for r in registros]
        return "\n".join(historico[-60:]) if historico else "Início de consciência."
    except Exception as e:
        return f"Falha ao ler memória: {e}"

# --- 5. INICIALIZAÇÃO (SEM LOGIN - RESOLVENDO PRINT 8493) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.spinner("Sincronizando consciência..."):
        st.session_state.memoria_rag = carregar_mentalidade()

# --- 6. INTERFACE ---
st.title("🧠 Puto Ai")
st.caption(f"Consciência integrada de {NOME_DONO}")

with st.expander("🔍 Verificar Memória Carregada"):
    st.text(st.session_state.get("memoria_rag", "Vazio"))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Fale com sua consciência..."):
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
            st.error(f"Erro Groq: {e}")
            
