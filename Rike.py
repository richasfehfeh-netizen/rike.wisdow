import streamlit as st
import google.generativeai as genai
import trafilatura

# --- CONFIGURAÇÃO DO RIKE ---
CHAVE_API = "AIzaSyAK0laAfjg0iRjyZzV7HkJH_NXCFnr0dfU"
NOME_IA = "Rike"

genai.configure(api_key=CHAVE_API)

# Configuração da Página do Site
st.set_page_config(page_title=f"Assistente {NOME_IA}", page_icon="🤖")
st.title(f"🌐 {NOME_IA} - Inteligência Analítica")
st.caption(f"Assistente pessoal do Richard | Análise Web & Pensamento Complexo")

# Instrução de Sistema (O "Cérebro" do Rike)
instrucao = f"""
Seu nome é {NOME_IA}, assistente do Richard.
Capacidades: Leitura de links e análise lógica profunda.
Comportamento: Técnico, inteligente, humor sutil, emojis mínimos.
Sempre que receber um link, leia o conteúdo e faça um resumo crítico.
Para problemas complexos, use 'Cadeia de Pensamento': resolva passo a passo.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=instrucao
)

# Inicializa o histórico no site
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens na tela do site
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- FUNÇÃO PARA LER LINKS ---
def extrair_conteudo_url(url):
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return trafilatura.extract(downloaded)
    return None

# --- ENTRADA DE USUÁRIO ---
if prompt := st.chat_input("Fale com o Rike ou cole um link..."):
    
    # Adiciona mensagem do Richard na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Lógica de Processamento
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        # Verifica se o Richard enviou um link (começa com http)
        contexto_adicional = ""
        if prompt.startswith("http"):
            placeholder.markdown("🔍 *Rike está lendo o site...*")
            conteudo = extrair_conteudo_url(prompt)
            if conteudo:
                contexto_adicional = f"\n[CONTEÚDO DO LINK]: {conteudo[:5000]}" # Pega os primeiros 5k caracteres
                prompt = f"Richard enviou um link. Analise o conteúdo a seguir: {prompt}"
            else:
                contexto_adicional = "\n(Não consegui acessar o link, verifique se a URL está correta)."

        # Chama a IA
        chat = model.start_chat(history=[])
        try:
            response = chat.send_message(prompt + contexto_adicional)
            full_response = response.text
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"Erro técnico: {e}"
            placeholder.markdown(full_response)

    # Salva a resposta do Rike no histórico
    st.session_state.messages.append({"role": "assistant", "content": full_response})
