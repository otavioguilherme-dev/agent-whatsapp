import streamlit as st
import requests
import json

# Configuração visual da página (deixa o visual limpo e profissional)
st.set_page_config(
    page_title="Suporte Técnico Virtual - OGNET BORRACHAS",
    page_icon="⚡",
    layout="centered"
)

# Estilização customizada para esconder menus padrões do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho da Página
# Versão corrigida e segura para o logotipo
try:
    st.image("https://ognetnauticos.com.br/wp-content/uploads/2024/logo.png", width=200)
except Exception:
    pass  # Se a imagem do site falhar ou não carregar, o app continua rodando sem quebrar
st.title("⚡ Assistente Técnico Virtual")
st.markdown("""
    Seja bem-vindo ao portal de suporte da **OGNET BORRACHAS**.  
    Aqui você pode diagnosticar problemas com a borracha/gaxeta da sua geladeira ou instalação de forma imediata.
""")

st.divider()

# --- LINK DO WEBHOOK FIXO (Nos bastidores) ---
# Cole aqui a URL definitiva do seu Webhook do Make.com (assim o cliente não vê)
WEBHOOK_URL = "SUA_URL_DO_MAKE_AQUI" 

# --- INTERACTION INTERFACE ---
st.subheader("Como podemos ajudar hoje?")

# Abas para o cliente escolher como quer enviar a informação
aba_texto, aba_foto = st.tabs(["✍️ Descrever Problema", "📸 Enviar Foto da Borracha"])

dado_para_enviar = ""
prosseguir = False

with aba_texto:
    texto_cliente = st.text_area(
        "Descreva detalhadamente o que está acontecendo (Ex: A borracha está soltando, o modelo da geladeira, etc.):",
        placeholder="Digite aqui seu relato..."
    )
    if st.button("Analisar Relato Textual", type="primary"):
        if texto_cliente.strip() == "":
            st.warning("Por favor, digite o problema antes de enviar.")
        else:
            dado_para_enviar = texto_cliente
            prosseguir = True

with aba_foto:
    # O Streamlit lida com upload de arquivos de forma nativa e segura
    foto_upload = st.file_uploader("Selecione ou tire uma foto nítida do encaixe ou da fresta da borracha:", type=["png", "jpg", "jpeg"])
    
    if foto_upload is not None:
        st.image(foto_upload, caption="Sua foto carregada com sucesso.", use_column_width=True)
        
        if st.button("Enviar Foto para Análise", type="primary"):
            # IMPORTANTE: Para o Gemini ler a imagem vinda da Web, o ideal é converter para um link público 
            # ou enviar o arquivo tratado. Para manter seu Make atual simples, você pode usar uma API temporária de imagem (como ImgBB)
            # ou ler o texto descritivo. 
            # Como teste inicial com o seu Make atual, você pode colar uma URL pública aqui:
            st.info("Processando imagem...")
            # Exemplo de integração simples enviando o binário ou link:
            dado_para_enviar = "https://sua-api-de-armazenamento.com/foto-temporaria.jpg" 
            prosseguir = True

# --- PROCESSAMENTO E RESPOSTA DA IA ---
if prosseguir:
    if WEBHOOK_URL == "SUA_URL_DO_MAKE_AQUI":
        st.error("Erro de configuração: O administrador precisa definir a URL do Webhook no código.")
    else:
        # Monta o mesmo JSON que o WhatsApp envia
        payload = {"foto": dado_para_enviar}
        
        with st.spinner("🤖 O Neto (Nosso Técnico Virtual) está analisando seu caso... Por favor, aguarde."):
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                
                if response.status_code == 200:
                    st.success("Análise concluída!")
                    st.subheader("📋 Diagnóstico e Instruções:")
                    
                    # Exibe a resposta do Gemini devolvida pelo Make
                    try:
                        resposta_json = response.json()
                        st.write(resposta_json.get("resposta_ia", response.text))
                    except ValueError:
                        st.write(response.text)
                        
                    st.balloons() # Efeito visual de sucesso
                else:
                    st.error(f"Houve um problema ao processar seu diagnóstico. (Código: {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                st.error("Não foi possível conectar ao servidor de IA. Tente novamente em instantes.")

st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
