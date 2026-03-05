import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz
import smtplib
import requests
import re
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CONFIGURAÇÕES DE ACESSO (MODIFIQUE AQUI) ---
# Coloquei a chave aqui para não depender mais dos Secrets
GROQ_CHAVE = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 

fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. INICIALIZAÇÃO DOS MOTORES ---
@st.cache_resource
def iniciar_sistema():
    # IA Groq (Usando a chave direta do código)
    client = Groq(api_key=GROQ_CHAVE)
    
    # Memória RAG (Planilha)
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            sheet = gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except:
        pass

    # Agendador (Corrigindo o fuso do print 8507)
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    return client, sheet, sch

client_ia, sheet_rag, scheduler = iniciar_sistema()

# --- 3. FUNÇÕES DE DISPARO ---
def enviar_push_real(msg):
    requests.post("https://ntfy.sh/calyo_push_notificator", data=msg.encode('utf-8'))

def enviar_email_real(assunto, corpo):
    try:
        user = st.secrets.get("EMAIL_USER")
        pw = st.secrets.get("EMAIL_PASS")
        if not user or not pw: return False
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = user
        msg['To'] = user
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(user, pw)
            s.send_message(msg)
        return True
    except: return False

# --- 4. RELATÓRIO E MEMÓRIA ---
def job_relatorio_diario():
    if sheet_rag:
        try:
            dados = sheet_rag.get_all_records()
            resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in dados[-10:]])
            enviar_email_real("📊 Relatório Calyo Assist", f"Resumo de hoje:\n\n{resumo}")
        except: pass

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio_diario, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE ---
st.title("🧠 Calyo Assist")
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    status_ferramentas = ""

    # E-mail
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Solicitação Richard", prompt):
            status_ferramentas += " [SISTEMA: E-mail enviado]"
            st.success("📧 E-mail enviado!")

    # Notificação (Resolve print 8507)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        min = int(num[0]) if num else 5
        data_f = agora + timedelta(minutes=min)
        scheduler.add_job(enviar_push_real, 'date', run_date=data_f, args=[f"Alerta: {prompt}"])
        status_ferramentas += f" [SISTEMA: Agendado para {data_f.strftime('%H:%M')}]"
        st.info(f"⏳ Agendado: {data_f.strftime('%H:%M')}")

    # RESPOSTA IA COM RAG (RESOLVE PRINT 8510)
    with st.chat_message("assistant"):
        memoria_texto = ""
        if sheet_rag:
            try:
                # Corrigido para evitar erro de sintaxe
                ultimos = sheet_rag.get_all_records()[-3:]
                memoria_texto = "Memória: " + " | ".join([str(u['content']) for u in ultimos])
            except: pass

        sys_msg = f"Nome: Calyo Assist. Dono: Richard. Status: {status_ferramentas}. {memoria_texto}"
        
        try:
            resp = client_ia.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
            )
            txt = resp.choices[0].message.content
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            # Salva na Planilha
            if sheet_rag:
                sheet_rag.append_row([agora.isoformat(), "user", prompt, txt])
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
    
