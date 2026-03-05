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
# Chave integrada para evitar o erro "IA Offline" (Print 8511)
CHAVE_GROQ = "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"
# Substitua pelo ID da sua planilha real
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 

fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. INICIALIZAÇÃO DOS MOTORES ---
@st.cache_resource
def iniciar_motores():
    # Inicializa Groq diretamente (Resolve Print 8508/8511)
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

# --- 3. FUNÇÕES DE EXECUÇÃO (MÉTODOS ATUALIZADOS) ---

def enviar_push_real(msg):
    """Envia notificação via ntfy com PRIORIDADE ALTA"""
    topic = "calyo_push_notificator"
    try:
        requests.post(
            f"https://ntfy.sh/{topic}", 
            data=msg.encode('utf-8'),
            headers={
                "Title": "⚠️ Calyo Assist - Alerta",
                "Priority": "high",  # Força prioridade máxima no Android/iOS
                "Tags": "brain,warning"
            }
        )
    except:
        pass

def enviar_email_real(assunto, corpo):
    """Método robusto para Gmail usando TLS e Porta 587"""
    try:
        user = st.secrets.get("EMAIL_USER")
        pw = st.secrets.get("EMAIL_PASS")
        
        if not user or not pw:
            return False
            
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = user
        msg['To'] = user 

        # Conexão segura 587 + TLS
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(user, pw)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no e-mail: {e}")
        return False

# --- 4. RELATÓRIO DIÁRIO (AUTOMAÇÃO ÀS 23:00) ---
def job_relatorio():
    if sheet_rag:
        try:
            dados = sheet_rag.get_all_records()
            resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in dados[-15:]])
            enviar_email_real("📊 Relatório Diário Calyo", f"Richard, aqui está o seu histórico de hoje:\n\n{resumo}")
        except: pass

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE E CHAT ---
st.title("🧠 Calyo Assist")
st.caption(f"Horário de Brasília: {datetime.now(fuso_br).strftime('%H:%M')}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    status_extra = ""

    # Lógica de E-mail (Ação Real)
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Solicitação Richard", f"Comando: {prompt}"):
            status_extra += " [SISTEMA: E-mail enviado com sucesso via Porta 587]"
            st.success("📧 E-mail enviado!")

    # Lógica de Agendamento (Resolve Print 8507)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        minutos = int(num[0]) if num else 5
        data_f = agora + timedelta(minutes=minutos)
        
        scheduler.add_job(
            enviar_push_real, 
            'date', 
            run_date=data_f, 
            args=[f"Lembrete Prioritário: {prompt}"]
        )
        status_extra += f" [SISTEMA: Notificação de ALTA PRIORIDADE agendada para {data_f.strftime('%H:%M')}]"
        st.info(f"⏳ Agendado para {data_f.strftime('%H:%M')}")

    # RESPOSTA DA IA COM RAG
    with st.chat_message("assistant"):
        contexto_memoria = ""
        if sheet_rag:
            try:
                # Puxa histórico recente da planilha (Resolve print 8510)
                ultimos = sheet_rag.get_all_records()[-3:]
                contexto_memoria = "Histórico: " + " | ".join([str(u['content']) for u in ultimos])
            except: pass

        sys_msg = f"Calyo Assist. Dono: Richard. Fuso: Brasília. Status: {status_extra}. {contexto_memoria}"
        
        try:
            resp = client_ia.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
            )
            txt = resp.choices[0].message.content
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            # Salva na Planilha para o RAG funcionar na próxima vez
            if sheet_rag:
                sheet_rag.append_row([agora.isoformat(), "user", prompt, txt])
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
    
