import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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"
client_groq = Groq(api_key=CHAVE_GROQ)

# ... (mantenha os imports e a chave Groq lá no topo)

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    # Abre a planilha e seleciona a primeira página
    return gc.open("Memoria_Rike").get_worksheet(0) 

try:
    sheet = conectar_planilha()
except Exception as e:
    st.error(f"Erro ao acessar a nuvem: {e}")
    st.info("Dica: Verifique se você compartilhou a planilha com o e-mail da Service Account!")
    st.stop()

# --- LOGIN E MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🔐 Rike - Memória de Nuvem")
    nome = st.text_input("Quem está acessando?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        # Busca histórico de forma segura
        try:
            todos = sheet.get_all_records()
            st.session_state.messages = [
                {"role": r["role"], "content": r["content"]} 
                for r in todos if str(r.get("user", "")) == nome
            ]
        except:
            # Se a planilha estiver vazia, começa do zero
            st.session_state.messages = []
            
        st.session_state.logado = True
        st.rerun()
    st.stop()
# ... (o restante do código do chat continua igual)

# --- CONEXÃO SEGURA COM GOOGLE SHEETS ---
def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Aqui ele busca os dados que você colou nos Secrets do Streamlit
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    return gc.open("Memoria_Rike").sheet1

try:
    sheet = conectar_planilha()
except Exception as e:
    st.error(f"Erro de Conexão com a Nuvem: {e}")
    st.stop()

# --- LOGIN E MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🔐 Rike - Memória de Nuvem")
    nome = st.text_input("Quem está acessando?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        # Busca histórico na planilha
        todos = sheet.get_all_records()
        st.session_state.messages = [
            {"role": r["role"], "content": r["content"]} 
            for r in todos if r["user"] == nome
        ]
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.title(f"🧠 Rike - Parceiro de {st.session_state.nome_usuario}")

# Exibe histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT ---
if prompt := st.chat_input("Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Salva na Planilha
    sheet.append_row([st.session_state.nome_usuario, "user", prompt])

    with st.chat_message("assistant"):
        instrucao = f"Seu nome é Rike. Parceiro de {st.session_state.nome_usuario}. Use o histórico para ser adaptativo e argumentativo."
        
        comp = client_groq.chat.completions.create(
            messages=[{"role": "system", "content": instrucao}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.8
        )
        
        resp = comp.choices[0].message.content
        st.markdown(resp)
        sheet.append_row([st.session_state.nome_usuario, "assistant", resp])
        st.session_state.messages.append({"role": "assistant", "content": resp})
        
