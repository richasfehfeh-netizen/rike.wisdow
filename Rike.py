import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÕES ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE SÉRIA E INTEGRADA ---
PROMPT_SISTEMA = """
Seu nome é Puto Ai. Você é uma inteligência séria e sensata integrada ao Richard.
REGRAS:
1. MEMÓRIA É REAL: Você possui acesso a um histórico de conversas. Use-o para reconhecer o Richard e saber o que já foi discutido.
2. SEM DESCULPAS: Nunca diga 'não tenho acesso' se houver contexto fornecido abaixo.
3. TOM: Sensato, parceiro e direto.
"""

# --- 3. LÓGICA DE RAG MELHORADA ---
def buscar_memoria_profunda(usuario):
    if not sheet: 
        return "Erro: Planilha não conectada."
    try:
        # Puxa tudo e garante que estamos filtrando pelo nome exato (sem espaços)
        todos = sheet.get_all_records()
        contexto = [f"{r['role']}: {r['content']}" for r in todos if str(r.get('user')).strip().lower() == usuario.strip().lower()]
        
        if not contexto:
            return "Nenhum histórico encontrado para este usuário."
        
        # Retorna as últimas 30 interações para dar uma base sólida
        return "\n".join(contexto[-30:])
    except Exception as e:
        return f"Erro ao ler memória: {e}"

# --- 4. LOGIN ---
if "logado" not in st.session_state:
    st.title("🧠 Puto Ai - Sincronização")
    nome = st.text_input("Richard, digite seu nome exatamente como na planilha:")
    if st.button("Sincronizar Consciência"):
        st.session_state.nome_usuario = nome
        # Força a busca da memória no momento do login
        with st.spinner("Puxando memórias da planilha..."):
            memoria = buscar_memoria_profunda(nome)
            st.session_state.contexto_rag = memoria
            st.session_state.logado = True
            st.session_state.messages = []
            st.rerun()
    st.stop()

# --- 5. INTERFACE ---
st.title("🧠 Puto Ai")

# Debug opcional: clique para ver o que a IA está "lembrando"
with st.expander("Visualizar Memória Carregada (RAG)"):
    st.text(st.session_state.get("contexto_rag", "Vazio"))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Fale com sua consciência..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Salva na planilha (Garanta que as colunas na Planilha sejam: user, chat, role, content)
    if sheet:
        try:
            sheet.append_row([st.session_state.nome_usuario, "Unica", "user", prompt])
        except:
            st.warning("Falha ao gravar na planilha.")

    with st.chat_message("assistant"):
        # Injeção Direta no Sistema
        contexto_atual = st.session_state.get("contexto_rag", "")
        mensagens_com_rag = [
            {"role": "system", "content": f"{PROMPT_SISTEMA}\n\nMEMÓRIA DO PASSADO:\n{contexto_atual}"}
        ] + st.session_state.messages

        try:
            comp = client.chat.completions.create(
                messages=mensagens_com_rag,
                model="llama-3.3-70b-versatile",
                temperature=0.5 # Menor para evitar que ele "alucine" que não sabe de nada
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([st.session_state.nome_usuario, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
        
