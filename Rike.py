import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO GROQ ---
# Substitua pela sua chave gsk_...
CHAVE_GROQ = "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" 
client = Groq(api_key=CHAVE_GROQ)

NOME_IA = "Rike"

st.set_page_config(page_title=f"Assistente {NOME_IA}", page_icon="⚡")
st.title(f"⚡ {NOME_IA} - Velocidade Máxima (Groq)")

# Instrução de Personalidade
instrucao_sistema = f"""
Seu nome é {NOME_IA}. Você é o assistente pessoal do Richard.
Você usa o modelo Llama 3 para processamento ultra rápido.
Seja técnico, inteligente e direto. Entenda gírias e contextos complexos.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do usuário
if prompt := st.chat_input("Fale com o Rike (Groq Edition)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Chamada para a API da Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucao_sistema},
                    *st.session_state.messages
                ],
                model="llama3-8b-8192", # Modelo super rápido e estável
            )
            
            response_text = chat_completion.choices[0].message.content
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
            
