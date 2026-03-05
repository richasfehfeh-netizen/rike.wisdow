import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz
import smtplib
import requests
import re
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CONFIGURAÇÕES DE TEMPO E INTERFACE ---
fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. MOTORES: IA (GEMINI) E PLANILHA ---
@st.cache_resource
def iniciar_sistema():
    # IA Nativa (Não precisa de chave Groq nos Secrets)
    # Usaremos o modelo configurado internamente
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # B. Conectar Planilha (Memória RAG)
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            # Substitua pelo seu ID real da planilha
            ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 
            sheet = gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except:
        pass

    # C. Agendador (Fuso Brasília - Resolve print 8507)
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    return model, sheet, sch

ia_model, sheet, scheduler = iniciar_sistema()

# --- 3. FUNÇÕES DE EXECUÇÃO REAL ---
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

# --- 4. RELATÓRIO DIÁRIO (ÀS 23:00) ---
def job_relatorio():
    if sheet:
        try:
            dados = sheet.get_all_records()
            resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in dados[-10:]])
            enviar_email_real("📊 Relatório Diário Calyo", f"Resumo de hoje:\n\n{resumo}")
        except: pass

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE DO CHAT ---
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

    # Lógica de E-mail
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Aviso Calyo Assist", prompt):
            status_ferramentas += " [E-mail enviado com sucesso]"
            st.success("📧 E-mail disparado!")

    # Lógica de Agendamento (Resolve print 8507)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        nums = re.findall(r'\d+', prompt)
        minutos = int(nums[0]) if nums else 5
        data_f = agora + timedelta(minutes=minutos)
        scheduler.add_job(enviar_push_real, 'date', run_date=data_f, args=[f"Alerta: {prompt}"])
        status_ferramentas += f" [Notificação real para {data_f.strftime('%H:%M')}]"
        st.success(f"⏳ Agendado para {data_f.strftime('%H:%M')}")

    # RESPOSTA DA IA COM MEMÓRIA RAG
    with st.chat_message("assistant"):
        # Recupera memória da planilha
        contexto_rag = ""
        if sheet:
            try:
                ultimos = sheet.get_all_records()[-3:]
                contexto_rag = "Contexto recente: " + " | ".join([u['content'] for u in ultimos])
            except: pass

        # Prompt de Sistema
        sys_p = f"Seu nome é Calyo Assist. Assistente do Richard. Status: {status_ferramentas}. {contexto_rag}"
        
        try:
            # Resposta via Gemini
            response = ia_model.generate_content(f"{sys_p}\n\nUsuário: {prompt}")
            txt = response.text
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            # Salva na Planilha para manter o RAG vivo
            if sheet:
                sheet.append_row([agora.isoformat(), "user", prompt])
                sheet.append_row([agora.isoformat(), "assistant", txt])
        except Exception as e:
            st.error(f"Erro na IA: {e}")
           
