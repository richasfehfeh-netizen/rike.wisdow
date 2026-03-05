import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re

# --- CONFIGURAÇÕES ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
TOPICO_NTFY = "calyo_assist_richard_2024" # Seu tópico do print 8495
NOME_DONO = "Richard"

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- MOTOR DE AGENDAMENTO (RESOLVENDO PRINT 8498) ---
@st.cache_resource
def iniciar_agendador():
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler

scheduler = iniciar_agendador()

def enviar_push(titulo, mensagem):
    requests.post(f"https://ntfy.sh/{TOPICO_NTFY}", 
                  data=mensagem.encode('utf-8'),
                  headers={"Title": titulo, "Priority": "high"})

# --- CONEXÃO (RESOLVENDO PRINT 8494) ---
@st.cache_resource
def conectar_planilha():
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
            return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
        return None
    except: return None

sheet = conectar_planilha()

# --- INTERFACE ---
st.title("🧠 Calyo Assist")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Comando para Calyo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Lógica de Agendamento
    if "agende" in prompt.lower() or "notifique" in prompt.lower():
        tempo = re.findall(r'\d+', prompt)
        if tempo:
            minutos = int(tempo[0])
            hora_f = (datetime.now() + timedelta(minutes=minutos)).strftime("%H:%M")
            scheduler.add_job(enviar_push, 'date', 
                              run_date=datetime.now() + timedelta(minutes=minutos), 
                              args=["Lembrete do Calyo", prompt])
            st.success(f"Tarefa agendada para às {hora_f}!")

    with st.chat_message("assistant"):
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "system", "content": "Seu nome é Calyo Assist. Você é um assistente sério."}] + st.session_state.messages,
                model="llama-3.3-70b-versatile"
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            st.session_state.messages.append({"role": "assistant", "content": resposta})
            if sheet: sheet.append_row([NOME_DONO, "Unica", "assistant", resposta])
        except Exception as e:
            st.error(f"Erro: {e}")
            
