import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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" 
client = Groq(api_key=CHAVE_GROQ)
NOME_IA = "Rike"

st.set_page_config(page_title=f"Assistente {NOME_IA}", page_icon="🤖")

# Inicialização das memórias da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = None

st.title(f"🤖 {NOME_IA} - Inteligência Analítica")

# 1. INICIATIVA DO RIKE: Pergunta o nome se for o primeiro acesso
if not st.session_state.nome_usuario:
    with st.chat_message("assistant"):
        st.markdown(f"Olá! Eu sou o **{NOME_IA}**. Como devo chamar você?")
    
    if nome := st.chat_input("Digite seu nome..."):
        st.session_state.nome_usuario = nome
        # O Rike já responde saudando o nome novo
        saudacao = f"Prazer em conhecer você, {nome}! Como posso ajudar hoje?"
        st.session_state.messages.append({"role": "assistant", "content": saudacao})
        st.rerun()
    st.stop()

# 2. INSTRUÇÃO DE SISTEMA (Melhorias pedidas pelo Rike na foto)
instrucao_sistema = f"""
Seu nome é {NOME_IA}. Você é o assistente pessoal de {st.session_state.nome_usuario}.
Melhorias aplicadas:
- Compreensão profunda de nuances e gírias do idioma.
- Base de conhecimento expandida e diálogos mais naturais.
- Capacidade de manter o contexto de conversas longas.
"""

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. ENTRADA DE CHAT NORMAL
if prompt := st.chat_input(f"Falar com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": instrucao_sistema}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erro: {e}")
            
