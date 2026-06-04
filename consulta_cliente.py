import streamlit as st
import requests
import json
import base64

# Configuração visual da página
st.set_page_config(
    page_title="Suporte Técnico Virtual - OGNET BORRACHAS",
    page_icon="⚡",
    layout="centered"
)

# --- CONFIGURAÇÕES DE INTEGRAÇÃO ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Estilização para esconder menus padrões
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho da Página
try:
    st.image("https://ognetnauticos.com.br/wp-content/uploads/2024/logo.png", width=200)
except Exception:
    pass  

st.title("⚡ Assistente Técnico Virtual")
st.markdown("""
    Seja bem-vindo ao portal de suporte da **%s**.  
    Anexe a foto da sua borracha ou da etiqueta de fabricação e descreva sua dúvida abaixo para uma análise imediata.
""" % "OGNET BORRACHAS")

st.divider()

st.subheader("📋 Envie os dados do seu produto")

# --- ENTRADA ÚNICA: FOTO + TEXTO LADO A LADO OU CONCATENADOS ---
foto_upload = st.file_uploader("📸 1. Selecione ou tire uma foto nítida (da etiqueta ou do problema na borracha):", type=["png", "jpg", "jpeg"])

if foto_upload is not None:
    st.image(foto_upload, caption="Sua foto carregada.", width=300)

texto_cliente = st.text_area(
    "✍️ 2. Descreva o que você precisa ou relate o problema:",
    placeholder="Ex: Minha geladeira é essa da foto, qual borracha comprar? / A borracha está soltando no canto superior...",
    key="relato_unico"
)

# Botão único de envio
if st.button("🚀 Iniciar Análise do Neto", type="primary", use_container_width=True):
    link_imagem_final = ""
    prosseguir = True
    
    # Validação mínima: o cliente precisa mandar pelo menos o texto ou a foto
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva seu problema antes de iniciar.")
        prosseguir = False
        
    if prosseguir:
        # Se houver foto, faz o upload para o ImgBB primeiro
        if foto_upload is not None:
            with st.spinner("🤖 Otimizando sua imagem..."):
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
                    else:
                        st.error("Erro ao processar imagem. Tentando enviar apenas o texto...")
                except Exception as e:
                    st.error(f"Falha ao carregar imagem: {e}")

        # Envia os dois dados estruturados para o Make
        payload = {
            "foto": link_imagem_final,
            "texto": texto_cliente.strip()
        }
        
        with st.spinner("🤖 O Neto está analisando seu caso... Por favor, aguarde."):
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                
                if response.status_code == 200:
                    st.success("Análise concluída!")
                    st.subheader("📋 Resposta do Técnico Neto:")
                    
                    try:
                        resposta_json = response.json()
                        st.write(resposta_json.get("resposta_ia", response.text))
                    except ValueError:
                        st.write(response.text)
                        
                    st.balloons() 
                else:
                    st.error(f"Houve um problema no servidor. (Código: {response.status_code})")
                    
            except requests.exceptions.RequestException:
                st.error("Não foi possível conectar ao motor de IA.")

st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
