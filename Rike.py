import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re

# --- CONFIGURAÇÕES TÉCNICAS ---
# Substitua pelos seus dados reais ou use st.secrets
CHAVE_GROQ = st.secrets.get("GROQ_API_KEY", "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")
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 
TOPICO_NTFY = "calyo_push_notificator" # Tópico do print 8495

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- MOTOR DE AGENDAMENTO (RESOLVE O ERRO DO PRINT 8498) ---
@st.cache_resource
def iniciar_agendador():
    scheduler = BackgroundScheduler()
    if not scheduler.running:
        scheduler.start()
    return scheduler

scheduler = iniciar_agendador()

def enviar_push_real(titulo, mensagem):
    """Envia a notificação para o celular via ntfy.sh"""
    try:
        requests.post(
            f"https://ntfy.sh/{TOPICO_NTFY}",
            data=mensagem.encode('utf-8'),
            headers={
                "Title": titulo,
                "Priority": "high",
                "Tags": "brain,bell"
            }
        )
    except Exception as e:
        print(f"Erro ao enviar push: {e}")

# --- CONEXÃO COM A PLANILHA (RESOLVE O ERRO DO PRINT 8494) ---
@st.cache_resource
def conectar_planilha():
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
    return None

sheet = conectar_planilha()

# --- INTERFACE ---
st.title("🧠 Calyo Assist")
st.caption("Consciência integrada de Richard")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada do Usuário
if prompt := st.chat_input("Fale com o Calyo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # LÓGICA DE AGENDAMENTO AUTOMÁTICO
    comando_agendar = any(palavra in prompt.lower() for palavra in ["agende", "notifique", "lembre", "avise"])
    
    if comando_agendar:
        numeros = re.findall(r'\d+', prompt)
        minutos = int(numeros[0]) if numeros else 5 # Padrão 5 min se não disser
        
        hora_disparo = datetime.now() + timedelta(minutes=minutos)
        
        # Agenda a tarefa real no servidor
        scheduler.add_job(
            enviar_push_real, 
            'date', 
            run_date=hora_disparo, 
            args=["Lembrete do Calyo Assist", f"Richard, você pediu: {prompt}"]
        )
        st.success(f"✅ Entendido! Notificação agendada para às {hora_disparo.strftime('%H:%M')}.")

    # RESPOSTA DA IA
    with st.chat_message("assistant"):
        try:
            # Instrução de Sistema para evitar a "amnésia" do print 8499
            instrucao_sistema = (
                "Seu nome é Calyo Assist. Você é o assistente pessoal do Richard. "
                "VOCÊ TEM capacidade de agendar notificações reais usando o ntfy.sh. "
                "Se o usuário pedir um lembrete, confirme que o agendador interno foi acionado."
            )
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": instrucao_sistema}] + st.session_state.messages
            )
            
            resposta_texto = response.choices[0].message.content
            st.markdown(resposta_texto)
            st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
            
            # Salva na planilha se disponível (Print 8494)
            if sheet:
                sheet.append_row([datetime.now().isoformat(), "Richard", prompt, resposta_texto])
                
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
            
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURAÇÃO DE E-MAIL ---
EMAIL_REMETENTE = "richasfehfeh@gmail.com" # Seu Gmail
SENHA_APP_GOOGLE = st.secrets.get("EMAIL_PASSWORD", "cmcg obth quqm fpxy") # A senha de 16 dígitos

def enviar_email_formal(assunto, corpo_mensagem):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = EMAIL_REMETENTE # Envia para você mesmo como relatório
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(corpo_mensagem, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP_GOOGLE)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

# --- DENTRO DA LÓGICA DE RESPOSTA DA IA ---
if "envie um e-mail" in prompt.lower() or "relatório por e-mail" in prompt.lower():
    sucesso = enviar_email_formal(
        assunto=f"Relatório Calyo Assist - {datetime.now().strftime('%d/%m/%Y')}",
        corpo_mensagem=f"Richard, aqui está o que você solicitou:\n\n{prompt}"
    )
    if sucesso:
        st.success("📧 E-mail enviado com sucesso para sua caixa de entrada!")
        
