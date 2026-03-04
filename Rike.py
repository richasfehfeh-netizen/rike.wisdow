import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES INICIAIS ---
CHAVE_GROQ = "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" # Insira sua chave Groq
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" # Aquele código longo da URL

client_groq = Groq(api_key=CHAVE_GROQ)

# --- 2. CONEXÃO COM A NUVEM (GOOGLE SHEETS) ---
@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Usa os segredos configurados no Streamlit Cloud
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        gc = gspread.authorize(creds)
        # Tenta abrir pelo ID para evitar erro 404
        return gc.open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

sheet = conectar_planilha()

# Se não conectar, para o código aqui
if sheet is None:
    st.info("💡 Dica: Verifique se o ID da planilha está correto e se você compartilhou ela com o e-mail do JSON!")
    st.stop()

# --- 3. LÓGICA DE LOGIN ---
if "logado" not in st.session_state:
    st.title("🔐 Rike - Acesso à Memória")
    nome_input = st.text_input("Quem está falando?")
    if st.button("Acessar"):
        if nome_input:
            st.session_state.nome_usuario = nome_input
            try:
                # Busca conversas antigas deste usuário
                todos_registros = sheet.get_all_records()
                st.session_state.messages = [
                    {"role": r["role"], "content": r["content"]} 
                    for r in todos_registros if str(r.get("user", "")) == nome_input
                ]
            except:
                st.session_state.messages = []
            
            st.session_state.logado = True
            st.rerun()
    st.stop()

# --- 4. INTERFACE DO CHAT ---
st.title(f"🧠 Rike - Consciência de {st.session_state.nome_usuario}")

# Exibe o histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. PROCESSAMENTO DE MENSAGENS ---
if prompt := st.chat_input("Fale com sua IA..."):
    # 1. Mostra a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Salva na planilha imediatamente
    try:
        sheet.append_row([st.session_state.nome_usuario, "user", prompt])
    except:
        pass

    # 3. Resposta do Rike
    with st.chat_message("assistant"):
        instrucao = f"Seu nome é Rike. Você é o parceiro intelectual de {st.session_state.nome_usuario}. Seja adaptativo e argumentativo."
        
        try:
            chat_completion = client_groq.chat.completions.create(
                messages=[{"role": "system", "content": instrucao}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.8
            )
            
            resposta = chat_completion.choices[0].message.content
            st.markdown(resposta)
            
            # 4. Salva a resposta na planilha
            sheet.append_row([st.session_state.nome_usuario, "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
            
