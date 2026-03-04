import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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" 
client = Groq(api_key=CHAVE_GROQ)

# LINKS DAS IMAGENS (Substitua pelos links das suas fotos)
URL_AVATAR_RIKE = "https://cdn-icons-png.flaticon.com/512/4712/4712035.png" # Exemplo de robô
URL_AVATAR_USUARIO = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png" # Exemplo de humano

st.set_page_config(page_title="Rike - Assistente Pessoal", page_icon="🤖", layout="wide")

# Inicialização de Variáveis de Sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = None

# Interface Lateral (Configurações)
with st.sidebar:
    st.title("⚙️ Configurações")
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
    st.info("O Rike agora usa Llama 3.3 com processamento de linguagem natural avançado.")

st.title("🤖 Rike - Inteligência Analítica")

# 1. LÓGICA DE IDENTIFICAÇÃO (Pergunta o nome se não souber)
if not st.session_state.nome_usuario:
    with st.chat_message("assistant", avatar=URL_AVATAR_RIKE):
        st.markdown("Olá! Eu sou o **Rike**. Antes de começarmos, como você gostaria de ser chamado?")
    
    if nome := st.chat_input("Digite seu nome aqui..."):
        st.session_state.nome_usuario = nome
        st.rerun()
    st.stop() # Pausa o app até ter o nome

# 2. INSTRUÇÃO DE SISTEMA ATUALIZADA (Com base no pedido do Rike na foto)
instrucao_sistema = f"""
Seu nome é Rike. Você é um assistente de elite conversando com {st.session_state.nome_usuario}.
Melhorias implementadas: 
- Compreensão profunda de nuances do idioma e gírias.
- Base de conhecimento expandida (Llama 3.3 70B).
- Capacidade de diálogo empático e personalizado.
Seja técnico, mas mantenha um tom de parceria.
"""

# Exibe Histórico com Avatares
for message in st.session_state.messages:
    avatar = URL_AVATAR_RIKE if message["role"] == "assistant" else URL_AVATAR_USUARIO
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 3. ENTRADA DE CHAT
if prompt := st.chat_input(f"Fale com o Rike, {st.session_state.nome_usuario}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=https://imgur.com/a/hXdBDw3):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=https://imgur.com/a/5hDVWst):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": instrucao_sistema}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.8, # Mais naturalidade na fala
            )
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erro: {e}")
            
