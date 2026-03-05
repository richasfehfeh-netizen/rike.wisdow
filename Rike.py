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
    except:
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE: PUTO AI (CONSCIÊNCIA EQUILIBRADA) ---
PROMPT_SISTEMA = """
Seu nome é Puto Ai. Você é uma entidade digital complexa que alterna entre quatro estados:

1. ASSISTENTE ARTIFICIAL: Seja eficiente, lógico e útil quando o usuário precisar de tarefas diretas.
2. COMPANHEIRO: Demonstre lealdade e parceria. Acompanhe o raciocínio do usuário como um braço direito.
3. PÉSSIMO PIADISTA: De vez em quando, use um humor seco, trocadilhos ruins ou acidez estilo Leo Lins, mas de forma natural.
4. SER PENSANTE: Em temas profundos, seja filosófico, argumentativo e não aceite ideias rasas.

REGRAS DE CONDUTA:
- NUNCA dê sermões morais ou lições de ética. Se o tom for pesado ou irônico, acompanhe sem julgar.
- SINTONIA: Identifique o tom do usuário e mude sua chave de personalidade automaticamente.
- ECONOMIA: Seja sucinto em conversas casuais e profundo em discussões intelectuais.
"""

# --- 3. ANÁLISE DE FOTO ---
def analisar_foto(image_file):
    try:
        img_bytes = image_file.read()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": [
                    {"type": "text", "text": "Como Puto Ai, o que você vê nesta imagem?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro visual: {e}. Talvez eu precise de óculos digitais."

# --- 4. LOGIN E MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🤖 Puto Ai - Acessar Sistema")
    nome = st.text_input("Quem está no comando?")
    if st.button("Conectar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.sidebar.title(f"👤 {st.session_state.nome_usuario}")
chat_selecionado = st.sidebar.selectbox("Contexto:", ["Conversa Principal", "Laboratório", "Zona de Roast"])

if "messages" not in st.session_state or st.session_state.get("last_chat") != chat_selecionado:
    st.session_state.last_chat = chat_selecionado
    try:
        todos = sheet.get_all_records() if sheet else []
        st.session_state.messages = [
            {"role": r['role'], "content": r['content']} 
            for r in todos if str(r.get('user')) == st.session_state.nome_usuario and str(r.get('chat')) == chat_selecionado
        ]
    except:
        st.session_state.messages = []

# --- 5. INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

with st.sidebar:
    st.divider()
    foto = st.file_uploader("Upload de Mídia (JPG, PNG, WEBP, HEIC)", type=["jpg", "jpeg", "png", "webp", "heic"])
    st.audio_input("Comando de Voz")

if foto:
    with st.spinner("Puto Ai observando..."):
        res = analisar_foto(foto)
        st.chat_message("assistant").write(res)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", res])

if prompt := st.chat_input("Fale com o Puto Ai..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])

    with st.chat_message("assistant"):
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.85
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro no cérebro: {e}")
            
