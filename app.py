import streamlit as st
import requests
import json
import base64
import re

# Configuração visual da página (Modo centralizado tradicional)
st.set_page_config(
    page_title="Técnico de Instalação - OGNET",
    page_icon="🔧",
    layout="centered"  # Garante o layout em coluna única centralizada
)

# --- CONFIGURAÇÕES DO WEBHOOK ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Remove barras, menus padrões, oculta a sidebar e estiliza o card de resposta
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* Força o sumiço completo da barra lateral antiga */
    .resposta-card {
        background-color: #f8f9fa;
        border-left: 5px solid #FF4B4B;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Principal Centralizado
try:
    st.image("https://ognetborrachas.streamlit.app/~/+/media/38265db37548b0d424994d0517a2b3ae.jpg", width=150)
except Exception:
    pass  

st.title("🧰 Técnico de Instalação da OGNET BORRACHAS")
st.markdown("Envie fotos da sua instalação ou digite aqui o seu problema ou dúvida que o nosso Técnico vai te ajudar a solucionar.")
st.divider()

# --- FLUXO EM COLUNA ÚNICA (UM EMBAIXO DO OUTRO) ---
st.subheader("📋 Painel de Suporte Técnico")

# Passo 1: Upload da Imagem
st.markdown("### 📸 1. Envio da Foto (Opcional)")
st.caption("Tire ou anexe uma imagem nítida do problema na borracha (frestas, falta de magnetismo, folgas).")
foto_upload = st.file_uploader("Selecione a imagem do problema:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Foto do problema carregada com sucesso", width=400)
    st.divider()

# Passo 2: Relato do Problema
st.markdown("### ✍️ 2. O que está acontecendo?")
st.caption("Descreva detalhadamente o defeito ou comportamento da gaxeta para guiar o nosso especialista.")
texto_cliente = st.text_area(
    "Relato do cliente:",
    placeholder="Ex: Minha borracha está com uma fresta no canto superior direito após a instalação e o ímã parece não puxar...",
    height=150,
    label_visibility="collapsed",
    key="relato_suporte"
)

st.markdown("<br>", unsafe_allow_html=True)

# Botão de Ação (Largura Completa)
if st.button("🚀 Iniciar Análise do Especialista OGNET", type="primary", use_container_width=True):
    link_imagem_final = "sem_foto"
    prosseguir = True
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, relate o problema por texto ou envie uma foto antes de continuar.")
        prosseguir = False
        
    if prosseguir:
        if foto_upload is not None:
            with st.spinner("🤖 Otimizando e fazendo upload da imagem..."):
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

        with st.spinner("🤖 Encaminhando para o especialista técnico Otávio Guilherme... Por favor, aguarde."):
            try:
                response = requests.post(WEBHOOK_URL, data=payload, timeout=45)
                
                if response.status_code == 200:
                    resposta_ia = limpar_resposta_ia(response.text)
                    
                    if not resposta_ia.strip():
                        st.warning("⚠️ O Make processou o chamado, mas a resposta retornou em branco. Verifique a configuração do seu Gemini no Make.")
                    else:
                        st.success("Diagnóstico Técnico Concluído!")
                        
                        st.markdown('<div class="resposta-card">', unsafe_allow_html=True)
                        st.subheader("📋 Instruções e Soluções Recomendadas:")
                        st.markdown(resposta_ia)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.balloons()
                else:
                    st.error(f"Erro na comunicação com a IA. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Não foi possível conectar ao servidor de inteligência artificial.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Divisão Corporativa de Suporte Técnico Pós-Venda.")
