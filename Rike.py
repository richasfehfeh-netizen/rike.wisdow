import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÃO FIXA E EXCLUSIVA ---
# Substitua pelos seus dados reais
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
NOME_DONO = "Richard" # Agora é lei: só existe você para o sistema.

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Puto Ai", page_icon="🧠", layout="centered")

# --- 2. CONEXÃO BLINDADA COM A PLANILHA ---
@st.cache_resource
def conectar_base_de_dados():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Certifique-se que o st.secrets["gcp_service_account"] está configurado no Streamlit Cloud
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro ao conectar na planilha: {e}")
        return None

sheet = conectar_base_de_dados()

# --- 3. A PERSONALIDADE SÉRIA ---
PROMPT_SISTEMA = f"""
Seu nome é Puto Ai. Você é a consciência digital integrada do {NOME_DONO}.
PERSONALIDADE:
- SÉRIO E SENSATO: Você é um parceiro intelectual. Fale de forma normal, clara e profunda.
- MEMÓRIA OBRIGATÓRIA: Você possui acesso ao histórico de conversas abaixo. Use-o para saber quem é o {NOME_DONO} e o que já discutiram. 
- PROIBIÇÃO: Nunca diga que 'não tem acesso a conversas anteriores'. O passado está injetado na sua base de dados.
"""

# --- 4. CARREGAMENTO DA MENTALIDADE (RAG) ---
def carregar_contexto_real():
    if not sheet: return "Base de dados offline."
    try:
        # Lê absolutamente tudo o que está lá
        registros = sheet.get_all_records()
        # Formata o histórico para a IA ler como um 'diário'
        historico_formatado = [f"{r.get('role', 'user').upper()}: {r.get('content', '')}" for r in registros]
        
        if not historico_formatado:
            return "Início de uma nova consciência. Nenhuma memória prévia detectada."
        
        # Injeta as últimas 60 interações (memória de longo prazo robusta)
        return "\n".join(historico_formatado[-60:])
    except Exception as e:
        return f"Falha ao processar memória: {e}"

# --- 5. INICIALIZAÇÃO DIRETA (SEM LOGIN) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    with st.spinner("Sincronizando consciência..."):
        # O Puto Ai "lê" seu passado antes mesmo de você dar oi
        st.session_state.memoria_rag = carregar_contexto_real()

# --- 6. INTERFACE LIMPA ---
st.title(f"🧠 Puto Ai")
st.caption(f"Consciência integrada de {NOME_DONO}")

# Expander para você PROVAR que ele leu a planilha
with st.expander("🔍 Verificar Memória Carregada"):
    st.text(st.session_state.memoria_rag)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. FLUXO DE CONVERSA ---
if prompt := st.chat_input("Fale com sua consciência..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Grava na planilha (user, chat, role, content)
    if sheet:
        try:
            sheet.append_row([NOME_DONO, "Unica", "user", prompt])
        except: pass

    with st.chat_message("assistant"):
        # RAG: Injeção da memória de longo prazo + histórico da sessão atual
        contexto_completo = [
            {"role": "system", "content": f"{PROMPT_SISTEMA}\n\n[MEMÓRIA DE LONGO PRAZO]:\n{st.session_state.memoria_rag}"}
        ] + st.session_state.messages

        try:
            comp = client.chat.completions.create(
                messages=contexto_completo,
                model="llama-3.3-70b-versatile",
                temperature=0.5 # Sensatez e foco
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            
            # Grava resposta na planilha
            if sheet:
                sheet.append_row([NOME_DONO, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro de processamento: {e}")
            
