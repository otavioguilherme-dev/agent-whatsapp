import streamlit as st
import requests
import json
import base64
import re

# Configuração visual da página (Modo amplo e focado no usuário)
st.set_page_config(
    page_title="Suporte Técnico OGNET BORRACHAS",
    page_icon="🔧",
    layout="wide"
)

# --- CONFIGURAÇÕES DO AGENTE DE SUPORTE ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Ocultar menus padrões do Streamlit e aplicar o estilo do card de resposta
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .resposta-card {
        background-color: #f8f9fa;
        border-left: 5px solid #FF4B4B;
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Layout do Cabeçalho
with st.container():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        try:
            st.image("https://ognetborrachas.streamlit.app/~/+/media/38265db37548b0d424994d0517a2b3ae.jpg", width=120)
        except Exception:
            pass  
    with col_titulo:
        st.title("🔧 Tecnico de Instalação da OGNET BORRACHAS")
        st.markdown("Envie fotos da sua instalação ou digite aqui o seu problema ou dúvida que o nosso Técnico vai te ajudar a solucionar.")

st.divider()

# --- DIVISÃO DA TELA EM COLUNAS LADO A LADO ---
st.subheader("📋 Preencha os dados do seu atendimento")
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📸 Passo 1: Envio Visual")
    st.caption("Tire ou anexe uma foto nítida do problema constatado na instalação (Ex: frestas, folgas, borracha desalinhada).")
    foto_upload = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if foto_upload is not None:
        st.markdown("---")
        st.image(foto_upload, caption="⚡ Visualização da imagem carregada", use_container_width=True)

with col2:
    st.markdown("### ✍️ Passo 2: Relato Técnico")
    st.caption("Descreva detalhadamente o comportamento da borracha ou do equipamento para a IA.")
    texto_cliente = st.text_area(
        "",
        placeholder="Ex: Instalei a borracha nova hoje na porta superior, mas ficou uma fresta no canto direito. O ímã parece fraco. O que devo fazer?",
        height=180,
        label_visibility="collapsed",
        key="relato_suporte"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Botão principal ocupando a largura total abaixo das colunas
if st.button("🚀 Iniciar Diagnóstico do Especialista OGNET", type="primary", use_container_width=True):
    link_imagem_final = "sem_foto"
    prosseguir = True
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva detalhadamente o problema antes de iniciar.")
        prosseguir = False
        
    if prosseguir:
        if foto_upload is not None:
            with st.spinner("🤖 Processando imagem do problema..."):
                try:
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    imgbb_url = "https://api.imgbb.com/1/upload"
                    payload_imgbb = {
                        "key": IMGBB_API_KEY,
                        "image": base64_image,
                        "expiration": 600 
                    }
                    
                    res_imgbb = requests.post(imgbb_url, data=payload_imgbb)
                    res_data = res_imgbb.json()
                    
                    if res_imgbb.status_code == 200 and res_data.get("success"):
                        link_imagem_final = res_data["data"]["url"]
                except Exception as e:
                    st.error(f"Erro no processamento da imagem: {e}")

        payload = {
            "foto": link_imagem_final,
            "texto": texto_cliente.strip()
        }
        
        def limpar_resposta_ia(texto_bruto):
            if not isinstance(texto_bruto, str):
                return ""
            texto = texto_bruto.strip()
            texto = re.sub(r'^\{\s*"(resposta_ia|result)"\s*:\s*["\']', '', texto)
            
            for delimitador in ['","thoughtSignature"', '"thoughtSignature"', '","role"', '"finishReason"', '","candidates"']:
                if delimitador in texto:
                    texto = texto.split(delimitador, 1)[0]
                    
            texto = texto.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '    ')
            texto = texto.strip()
            while texto.endswith('}') or texto.endswith('"') or texto.endswith("'") or texto.endswith(']'):
                if texto.endswith('}') or texto.endswith(']'): texto = texto[:-1].strip()
                if texto.endswith('"') or texto.endswith("'"): texto = texto[:-1].strip()
            return texto.strip()

        with st.spinner("🤖 O especialista Otávio Guilherme está avaliando o seu caso... Aguarde."):
            try:
                response = requests.post(WEBHOOK_URL, data=payload, timeout=45)
                
                if response.status_code == 200:
                    resposta_ia = limpar_resposta_ia(response.text)
                    
                    if not resposta_ia.strip():
                        st.warning("⚠️ O servidor respondeu, mas o diagnóstico retornou vazio. Verifique a rota no Make.")
                    else:
                        st.success("Análise de Suporte Concluída!")
                        
                        st.markdown('<div class="resposta-card">', unsafe_allow_html=True)
                        st.subheader("📋 Diagnóstico & Instruções do Especialista:")
                        st.markdown(resposta_ia)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.balloons()
                else:
                    st.error(f"Não foi possível obter resposta do servidor. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Falha de comunicação com o motor de inteligência artificial.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Divisão Corporativa de Suporte Técnico Pós-Venda.")
