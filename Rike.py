import streamlit as st
import google.generativeai as genai
import trafilatura

# --- CONFIGURAÇÃO ---
CHAVE_API = "AIzaSyAK0laAfjg0iRjyZzV7HkJH_NXCFnr0dfU"
NOME_IA = "Rike"
genai.configure(api_key=CHAVE_API)

st.set_page_config(page_title=f"Assistente {NOME_IA}", page_icon="🤖")
st.title(f"🌐 {NOME_IA} - Inteligência Analítica")

# Lógica de Auto-Detect do Modelo (Evita o erro 404)
@st.cache_resource
def get_model():
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    nome_modelo = modelos[0]
    instrucao = f"Seu nome é {NOME_IA}, assistente do Richard. Seja técnico e inteligente."
    return genai.GenerativeModel(model_name=nome_modelo, system_instruction=instrucao)

model = get_model()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        chat = model.start_chat(history=[])
        response = chat.send_message(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
