import streamlit as st
import requests
import json
import base64

# Configuração visual da página (deixa o visual limpo e profissional)
st.set_page_config(
    page_title="Suporte Técnico Virtual - OGNET BORRACHAS",
    page_icon="⚡",
    layout="centered"
)

# --- CONFIGURAÇÕES DE INTEGRAÇÃO (DEFINITIVAS) ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"  # Seu link do Make correto
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"                          # Sua chave do ImgBB correta

# Estilização customizada para esconder menus padrões do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho da Página com tratamento seguro para o logotipo
try:
    st.image("https://ognetnauticos.com.br/wp-content/uploads/2024/logo.png", width=200)
except Exception:
    pass  

st.title("⚡ Assistente Técnico Virtual")
st.markdown("""
    Seja bem-vindo ao portal de suporte da **OGNET BORRACHAS**.  
    Aqui você pode diagnosticar problemas com a borracha/gaxeta da sua geladeira ou instalação de forma imediata.
""")

st.divider()

# --- INTERACTION INTERFACE ---
st.subheader("Como podemos ajudar hoje?")

# Abas para o cliente escolher como quer enviar a informação
aba_texto, aba_foto = st.tabs(["✍️ Descrever Problema", "📸 Enviar Foto da Borracha"])

dado_para_enviar = ""
prosseguir = False

# --- TRATAMENTO DO INPUT POR TEXTO ---
with aba_texto:
    texto_cliente = st.text_area(
        "Descreva detalhadamente o que está acontecendo (Ex: A borracha está soltando, o modelo da geladeira, etc.):",
        placeholder="Digite aqui seu relato...",
        key="txt_area_suporte"
    )
    if st.button("Analisar Relato Textual", type="primary", key="btn_suporte_txt"):
        if texto_cliente.strip() == "":
            st.warning("Por favor, digite o problema antes de enviar.")
        else:
            dado_para_enviar = texto_cliente
            prosseguir = True

# --- TRATAMENTO DO INPUT POR FOTO (UPLOAD AUTOMÁTICO VIA IMGBB) ---
with aba_foto:
    foto_upload = st.file_uploader("Selecione ou tire uma foto nítida do encaixe ou da fresta da borracha:", type=["png", "jpg", "jpeg"])
    
    if foto_upload is not None:
        st.image(foto_upload, caption="Sua foto carregada com sucesso.", use_column_width=True)
        
        if st.button("Enviar Foto para Análise", type="primary", key="btn_suporte_foto"):
            with st.spinner("🤖 Processando e otimizando sua imagem..."):
                try:
                    # Transforma o arquivo carregado em Base64 para enviar ao ImgBB
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    # Envia a foto para a API do ImgBB (com expiração de 10 minutos por privacidade)
                    imgbb_url = "https://api.imgbb.com/1/upload"
                    payload_imgbb = {
                        "key": IMGBB_API_KEY,
                        "image": base64_image,
                        "expiration": 600 
                    }
                    
                    res_imgbb = requests.post(imgbb_url, data=payload_imgbb)
                    res_data = res_imgbb.json()
                    
                    if res_imgbb.status_code == 200 and res_data.get("success"):
                        # Captura o link HTTP público da imagem gerada pelo ImgBB
                        dado_para_enviar = res_data["data"]["url"]
                        prosseguir = True
                    else:
                        st.error("Erro ao converter a imagem no servidor. Tente reenviar o arquivo.")
                except Exception as e:
                    st.error(f"Falha no processamento interno da imagem: {e}")

# --- PROCESSAMENTO E ENVIO PARA O MAKE.COM ---
if prosseguir:
    # Monta o JSON padrão esperado pelo seu cenário do Make
    payload = {"foto": dado_para_enviar}
    
    with st.spinner("🤖 O Neto (Nosso Técnico Virtual) está analisando seu caso... Por favor, aguarde."):
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
            
            if response.status_code == 200:
                st.success("Análise concluída!")
                st.subheader("📋 Diagnóstico e Instruções:")
                
                # Tenta exibir a chave 'resposta_ia' devolvida pelo Webhook Response do Make
                try:
                    resposta_json = response.json()
                    st.write(resposta_json.get("resposta_ia", response.text))
                except ValueError:
                    st.write(response.text)
                    
                st.balloons() 
            else:
                st.error(f"Houve um problema ao processar seu diagnóstico. (Código de erro do servidor: {response.status_code})")
                
        except requests.exceptions.RequestException:
            st.error("Não foi possível conectar ao motor de IA. Tente novamente em instantes.")

st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
