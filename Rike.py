import streamlit as st
import smtplib
import requests
import re
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES DE SEGURANÇA (SECRETS) ---
CHAVE_GROQ = st.secrets.get("GROQ_API_KEY")
EMAIL_USER = st.secrets.get("EMAIL_USER")
EMAIL_PASS = st.secrets.get("EMAIL_PASS")
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 
TOPICO_NTFY = "calyo_push_notificator"

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Calyo Assist", page_icon="🧠", layout="centered")

# --- 2. MOTORES INTERNOS (AGENDADOR E PLANILHA) ---
@st.cache_resource
def iniciar_motores():
    # Agendador
    sch = BackgroundScheduler()
    if not sch.running: sch.start()
    
    # Planilha (RAG)
    sheet_obj = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            sheet_obj = gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except: pass
    return sch, sheet_obj

scheduler, sheet = iniciar_motores()

# --- 3. FUNÇÕES DE COMUNICAÇÃO EXTERNA ---
def enviar_push(mensagem):
    requests.post(f"https://ntfy.sh/{TOPICO_NTFY}", data=mensagem.encode('utf-8'))

def enviar_email(assunto, mensagem):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- 4. INTERFACE ---
st.title("🧠 Calyo Assist")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. LÓGICA DE PROCESSAMENTO ---
if prompt := st.chat_input("Fale com o Calyo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ação: Agendamento
    if any(x in prompt.lower() for x in ["agende", "avise", "lembre"]):
        minutos = re.findall(r'\d+', prompt)
        tempo = int(minutos[0]) if minutos else 5
        hora_alerta = datetime.now() + timedelta(minutes=tempo)
        scheduler.add_job(enviar_push, 'date', run_date=hora_alerta, args=[f"Lembrete: {prompt}"])
        st.success(f"✅ Agendado para às {hora_alerta.strftime('%H:%M')}")

    # Ação: E-mail
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email("Relatório Calyo Assist", prompt):
            st.success("📧 E-mail enviado!")

    # Resposta da IA
    with st.chat_message("assistant"):
        instrucao = f"Seu nome é Calyo Assist. Você é o assistente do Richard. Você PODE enviar e-mails e push via ntfy ({TOPICO_NTFY})."
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": instrucao}] + st.session_state.messages
            )
            texto = resp.choices[0].message.content
            st.markdown(texto)
            st.session_state.messages.append({"role": "assistant", "content": texto})
            if sheet: sheet.append_row([datetime.now().isoformat(), "Richard", prompt, texto])
        except Exception as e:
            st.error(f"Erro: {e}")
        
