import streamlit as st
import requests
import json
import base64
import re

# Configuração visual da página
st.set_page_config(
    page_title="Suporte Técnico OGNET BORRACHAS",
    page_icon="🔧",
    layout="centered"
)

# --- CONFIGURAÇÕES DO AGENTE DE SUPORTE ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Ocultar menus padrões do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

try:
    st.image("https://ognetborrachas.streamlit.app/~/+/media/38265db37548b0d424994d0517a2b3ae.jpg", width=200)
except Exception:
    pass  

st.title("🔧 Especialista Técnico - OGNET BORRACHAS")
st.markdown("Portal de apoio ao cliente. Envie fotos ou detalhes do seu problema de instalação para receber um diagnóstico na hora.")
st.divider()

st.subheader("📋 Descreva o problema ou envie uma foto da sua instalação")

foto_upload = st.file_uploader("📸 Caso queira, tire ou envie uma foto nítida do problema (frestas, folgas, borracha que não gruda):", type=["png", "jpg", "jpeg"])

if foto_upload is not None:
    st.image(foto_upload, caption="Sua foto carregada.", width=300)

texto_cliente = st.text_area(
    "✍️ Relate o que está acontecendo com a sua borracha:",
    placeholder="Ex: Troquei a borracha mas ficou uma fresta no canto superior, o que eu faço? ou o ímã está muito fraco.",
    key="relato_suporte"
)

def limpar_resposta_ia(texto_bruto):
    if not isinstance(texto_bruto, str):
        return ""
    
    texto = texto_bruto.strip()
    
    # Remove marcações de chaves estruturadas que o Make envie por acidente
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


if st.button("🚀 Solicitar Ajuda do Especialista OGNET", type="primary", use_container_width=True):
    link_imagem_final = "sem_foto"
    prosseguir = True
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva detalhadamente o problema.")
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
                    st.error(f"Erro no processamento visual: {e}")

        # Payload limpo e direto enviado ao Make
        payload = {
            "foto": link_imagem_final,
            "texto": texto_cliente.strip()
        }
        
        with st.spinner("🤖 O especialista OGNET está analisando seu caso... Por favor, aguarde."):
            try:
                # Envio padrão estruturado via formulário de dados
                response = requests.post(WEBHOOK_URL, data=payload, timeout=45)
                
                if response.status_code == 200:
                    resposta_ia = limpar_resposta_ia(response.text)
                    
                    if not resposta_ia.strip():
                        st.warning("⚠️ O servidor técnico processou a requisição, mas a resposta retornou vazia. Verifique a rota ativa no Make.")
                    else:
                        st.success("Análise Concluída!")
                        st.subheader("📋 Instruções do Especialista Otávio Guilherme:")
                        st.markdown(resposta_ia)
                else:
                    st.error(f"Não foi possível obter resposta do servidor técnico. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Falha de comunicação com o motor de inteligência artificial.")

st.divider()
st.caption("© 2026 OGNET BORRACHAS - Divisão de Suporte Técnico Pós-Venda.")
