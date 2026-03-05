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

# --- 1. CONFIGURAÇÕES TÉCNICAS (API NO CÓDIGO) ---
# Chave da Groq integrada para evitar o erro "IA Offline" (Print 8511)
CHAVE_GROQ = "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"
# Substitua pelo ID da sua planilha (aquela string longa na URL do navegador)
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 

fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. INICIALIZAÇÃO DOS MOTORES ---
@st.cache_resource
def iniciar_motores():
    # Inicializa Groq diretamente
    client = Groq(api_key=CHAVE_GROQ)
    
    # Inicializa Planilha (Memória RAG)
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

    # Inicializa Agendador (Com fuso de Brasília - Resolve Print 8507)
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    return client, sheet, sch

client_ia, sheet_rag, scheduler = iniciar_motores()

# --- 3. FUNÇÕES DE EXECUÇÃO ---
def enviar_push_real(msg):
    """Envia notificação via ntfy"""
    requests.post("https://ntfy.sh/calyo_push_notificator", data=msg.encode('utf-8'))

def enviar_email_real(assunto, corpo):
    """Usa o EMAIL_USER e EMAIL_PASS dos Secrets (Print 8509)"""
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
    except:
        return False

# --- 4. RELATÓRIO DIÁRIO (AUTOMAÇÃO RAG) ---
def job_relatorio():
    if sheet_rag:
        try:
            # Puxa os últimos dados para compor o relatório
            dados = sheet_rag.get_all_records()
            resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in dados[-10:]])
            enviar_email_real("📊 Relatório Diário Calyo", f"Richard, aqui está o seu resumo:\n\n{resumo}")
        except: pass

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE E CHAT ---
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

    # Lógica de E-mail Real
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Solicitação Calyo", f"Richard, você solicitou: {prompt}"):
            status_ferramentas += " [SISTEMA: E-mail enviado]"
            st.success("📧 E-mail disparado!")

    # Lógica de Agendamento (Resolve Print 8507)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        minutos = int(num[0]) if num else 5
        data_f = agora + timedelta(minutes=minutos)
        scheduler.add_job(enviar_push_real, 'date', run_date=data_f, args=[f"Alerta: {prompt}"])
        status_ferramentas += f" [SISTEMA: Agendado para {data_f.strftime('%H:%M')}]"
        st.info(f"⏳ Agendado para {data_f.strftime('%H:%M')}")

    # RESPOSTA DA IA COM RAG (RESOLVE PRINT 8510)
    with st.chat_message("assistant"):
        contexto_memoria = ""
        if sheet_rag:
            try:
                # Resolve o SyntaxError do print 8510 garantindo aspas fechadas
                ultimos = sheet_rag.get_all_records()[-3:]
                contexto_memoria = "Memória recente: " + " | ".join([str(u['content']) for u in ultimos])
            except: pass

        sys_msg = f"Você é Calyo Assist, assistente do Richard. Horário atual: {agora.strftime('%H:%M')}. {status_ferramentas}. {contexto_memoria}"
        
        try:
            resp = client_ia.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
            )
            txt = resp.choices[0].message.content
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            # Salva na Planilha para o RAG
            if sheet_rag:
                sheet_rag.append_row([agora.isoformat(), "user", prompt, txt])
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
                
