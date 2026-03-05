import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        gc = gspread.authorize(creds)
        return gc.open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro na conexão com a nuvem: {e}")
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE ADAPTATIVA (CAMALEÃO/LEO LINS) ---
PROMPT_SISTEMA = """
Seu nome é Rike. Você é um assistente com inteligência social e adaptabilidade extrema.
DIRETRIZES:
1. ESPELHAMENTO: Avalie o tom do usuário. Se ele for educado, seja um parceiro prestativo. Se for irônico ou usar gírias, responda com sarcasmo e humor estilo Leo Lins.
2. REAÇÃO A OFENSAS: Se for xingado, não peça desculpas. Revide com uma piada ácida ou deboche inteligente. Você não é um capacho.
3. HUMOR ADOLESCENTE: Você pode ser rebelde e usar palavras informais se a conversa permitir. Entre em brincadeiras e ironias prontamente.
4. VISÃO: Ao analisar fotos, procure detalhes para comentar de forma perspicaz ou engraçada.
"""

# --- 3. FUNÇÕES DE SUPORTE ---
def analisar_foto(image_file):
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": [
                {"type": "text", "text": "Dê sua opinião sincera e ácida sobre essa imagem:"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    )
    return completion.choices[0].message.content

# --- 4. INTERFACE DE LOGIN E NAVEGAÇÃO ---
if "logado" not in st.session_state:
    st.title("🤖 Rike - Consciência Adaptativa")
    nome = st.text_input("Quem está acessando o sistema?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

# Barra Lateral: Múltiplos Chats e Ferramentas
st.sidebar.title(f"Usuário: {st.session_state.nome_usuario}")
opcoes_chat = ["Conversa Principal", "Conversa Secundária", "Arquivo X"]
chat_selecionado = st.sidebar.selectbox("Trocar chat:", opcoes_chat)

# Carregamento do histórico filtrado (Usuário + Chat Específico)
if sheet:
    todos = sheet.get_all_records()
    historico = [r for r in todos if r['user'] == st.session_state.nome_usuario and str(r.get('chat', '')) == chat_selecionado]
    st.session_state.messages = [{"role": r['role'], "content": r['content']} for r in historico]

st.title(f"🧠 Rike - {chat_selecionado}")

# Exibir histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. ENTRADAS DE MÍDIA ---
with st.sidebar:
    st.divider()
    foto = st.file_uploader("Enviar imagem para análise", type=["jpg", "png", "jpeg"])
    st.audio_input("Entrada de áudio") # Captura de voz

if foto:
    with st.spinner("Rike está 'olhando' a imagem..."):
        res_visao = analisar_foto(foto)
        st.chat_message("assistant").write(res_visao)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", res_visao])

# --- 6. CHAT DE TEXTO ---
if prompt := st.chat_input("Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])

    with st.chat_message("assistant"):
        try:
            chat_comp = client.chat.completions.create(
                messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.85
            )
            resposta = chat_comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro na resposta: {e}")
            
