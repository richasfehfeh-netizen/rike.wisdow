import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
TOPICO_NTFY = "calyo_assist_richard_2024" # Seu tópico do print 8495
NOME_DONO = "Richard"

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Calyo Assist", page_icon="🧠", layout="centered")

# --- 2. MOTOR DE AGENDAMENTO E NOTIFICAÇÃO ---
if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.scheduler.start()

def enviar_push(titulo, mensagem):
    requests.post(f"https://ntfy.sh/{TOPICO_NTFY}", 
                  data=mensagem.encode('utf-8'),
                  headers={"Title": titulo, "Priority": "high", "Tags": "alarm_clock"})

def agendar_tarefa(mensagem, minutos):
    hora_envio = datetime.now() + timedelta(minutes=minutos)
    st.session_state.scheduler.add_job(
        enviar_push, 'date', run_date=hora_envio, args=["Lembrete Calyo", mensagem]
    )
    return hora_envio.strftime("%H:%M")

# --- 3. CONEXÃO E MEMÓRIA (RESOLVENDO PRINT 8494) ---
@st.cache_resource
def conectar_planilha():
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
            return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
        return None
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

sheet = conectar_planilha()

def carregar_contexto():
    if not sheet: return "Base offline. Corrija os Secrets."
    try:
        registros = sheet.get_all_records()
        return "\n".join([f"{r['role'].upper()}: {r['content']}" for r in registros][-50:])
    except: return "Erro ao ler histórico."

# --- 4. INTERFACE E PERSONALIDADE ---
st.title("🧠 Calyo Assist")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.memoria_rag = carregar_contexto()

with st.expander("🔍 Memória Carregada"):
    st.text(st.session_state.memoria_rag)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. PROCESSAMENTO DE COMANDO ---
if prompt := st.chat_input("Comando..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    if sheet: sheet.append_row([NOME_DONO, "Unica", "user", prompt])

    with st.chat_message("assistant"):
        # Lógica de Agendamento Automático
        tempo_match = re.search(r'(\d+)\s*(minuto|min)', prompt.lower())
        if "agende" in prompt.lower() or "notifique" in prompt.lower():
            if tempo_match:
                minutos = int(tempo_match.group(1))
                hora_f = agendar_tarefa(prompt, minutos)
                st.info(f"✅ Agendado para às {hora_f}")

        # Resposta da IA com RAG
        memoria = st.session_state.memoria_rag
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "system", "content": f"Seu nome é Calyo Assist. Seja sério. MEMÓRIA:\n{memoria}"}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([NOME_DONO, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro: {e}")
                                
