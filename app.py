import streamlit as st
import requests
import json
import base64
import re

# Configuração visual da página (Modo centralizado tradicional)
st.set_page_config(
    page_title="Agente de IA para Suporte Técnico e Instalação - OGNET-BORRACHAS",
    page_icon="🔧",
    layout="centered"
)

# --- CONFIGURAÇÕES DO WEBHOOK ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# CUSTOMIZAÇÃO CORES OGNET (Baseado em LOGO_BANNER.jpg)
# Azul Escuro: #1B2E7C | Laranja: #E96A23
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    /* Customização do Botão Principal (Estilo OGNET) */
    div.stButton > button:first-child {
        background-color: #E96A23 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #1B2E7C !important;
        box-shadow: 0px 4px 10px rgba(27, 46, 124, 0.3) !important;
    }
    
    /* Subtítulos em Azul Escuro */
    h1, h2, h3 {
        color: #1B2E7C !important;
    }
    
    /* Card de Resposta com a borda Laranja OGNET e fundo suave */
    .resposta-card {
        background-color: #f8f9fa;
        border-left: 6px solid #E96A23;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Principal Centralizado com Logo Local
try:
    # O Streamlit lê o arquivo "LOGO_BANNER.jpg" direto do seu diretório
    st.image("LOGO_BANNER.jpg", width=550)
except Exception as e:
    # Caso o arquivo não seja encontrado por algum motivo, exibe o título em texto
    st.warning("Carregando cabeçalho técnico...")

st.title("🧰 Agente de IA para Suporte Técnico e Instalação - OGNET-BORRACHAS")
st.markdown("Envie fotos da sua instalação ou digite aqui o seu problema ou dúvida que o nosso Especialista Técnico vai te ajudar a solucionar.")
st.divider()

# --- FLUXO EM COLUNA ÚNICA ---
st.subheader("📋 Painel de Suporte Técnico")

# Passo 1: Upload da Imagem do Problema
st.markdown("### 📸 1. Envio da Foto do Problema (Opcional)")
st.caption("Tire ou anexe uma imagem nítida do problema constatado (Ex: frestas na porta, borracha amassada, folgas).")
foto_upload = st.file_uploader("Selecione a imagem do problema:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Foto do problema carregada com sucesso", width=400)
    st.divider()

# Passo 2: Relato do Problema Técnico
st.markdown("### ✍️ 2. O que está acontecendo? Explique aqui qual é o problema ou duvida!")
st.caption("Descreva detalhadamente a duvida ou problema na sua borracha para guiar o nosso especialista técnico.")
texto_cliente = st.text_area(
    "Relato do cliente:",
    placeholder="Ex: Instalei a borracha nova hoje, mas ficou uma fresta de quase 1 centímetro no canto superior direito...",
    height=150,
    label_visibility="collapsed",
    key="relato_suporte"
)

st.markdown("<br>", unsafe_allow_html=True)

# Botão de Ação (Largura Completa com cores dinâmicas da OGNET)
if st.button("🚀 Iniciar Análise do Especialista Técnico da OGNET BORRACHAS", type="primary", use_container_width=True):
    link_imagem_final = "sem_foto"
    prosseguir = True
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, relate o problema por texto ou envie uma foto do defeito antes de continuar.")
        prosseguir = False
        
    if prosseguir:
        if foto_upload is not None:
            with st.spinner("🤖 Analisando e enviando imagem do problema..."):
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
            
            try:
                if texto.startswith('{'):
                    dados_json = json.loads(texto)
                    if "result" in dados_json:
                        return dados_json["result"].strip()
                    if "resposta_ia" in dados_json:
                        return dados_json["resposta_ia"].strip()
            except Exception:
                pass

            texto = re.sub(r'^\{\s*\\*"(resposta_ia|result)\\*"\s*:\s*\\*["\']', '', texto)
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
                        st.warning("⚠️ O sistema processou o chamado, mas o diagnóstico retornou vazio. Verifique a configuração no Make.")
                    else:
                        st.success("Análise de Suporte Concluída!")
                        
                        st.markdown('<div class="resposta-card">', unsafe_allow_html=True)
                        st.subheader("📋 Instruções Técnicas de Instalação:")
                        st.markdown(resposta_ia)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.balloons()
                else:
                    st.error(f"Erro na comunicação com a IA. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Não foi possível conectar ao servidor de inteligência artificial.")
# --- ADICIONE ESTE BLOCO NO FINAL DO SEU CÓDIGO DE SUPORTE ---

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.subheader("🛠️ Precisa de mais ajuda?")

# Criando duas colunas para os botões finais
col1, col2 = st.columns(2)

with col1:
    # Botão de redirecionamento direto para o WhatsApp comercial
    msg_whatsapp = "Olá! Vim pelo suporte do assistente virtual da OGNET e preciso de ajuda com meu pedido."
    link_wa = f"https://wa.me/5511994251306?text={requests.utils.quote(msg_whatsapp)}"
    
    st.markdown(
        f'<a href="{link_wa}" target="_blank">'
        '<button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:16px;">'
        '💬 Falar com Atendente no WhatsApp'
        '</button></a>',
        unsafe_allow_html=True
    )

with col2:
    # Botão que abre as instruções de devolução inteligente
    if st.button("❌ Quero Devolver / Cancelar meu Pedido", use_container_width=True):
        st.info("💡 **Instruções para Devolução Rápida e Gratuita:**")
        st.markdown("""
        Se a sua compra foi realizada pelo **Mercado Livre** ou **Shopee**, você pode devolver o produto de forma totalmente gratuita e receber seu reembolso imediato seguindo o passo a passo abaixo:
        
        ### 📦 No Mercado Livre:
        1. Vá em **Minhas Compras** e clique no seu pedido da OGNET.
        2. Escolha a opção **Devolver o produto**.
        3. Selecione exatamente um destes motivos:
           * **"É o que eu comprei, mas não me serve"**
           * **"Me arrependi da compra"**
        # Caso ja tenha aberto uma reclamação cancele e faça uma nova abertura com os motivos listados acima #
        4. O Mercado Livre vai gerar uma etiqueta de envio gratuita para você despachar nos Correios ou agência parceira.
        
        ---
        
        ### 🛒 Na Shopee:
        1. Vá em **Eu** > **Minhas Compras** > **A Caminho/Entregue** e clique no pedido.
        2. Clique no botão **Pedir Reembolso/Devolução** (Atenção: Não clique em 'Pedido Recebido' antes disso).
        3. No motivo da devolução, selecione:
           * **"Mudança de ideia"** ou **"Não preciso mais do produto"**
        4. Selecione a opção de frete reverso gratuito oferecido pela Shopee e leve o código ao posto indicado.
        
        ---
        
        ⚠️ **Atenção:** Selecionar outros motivos que não sejam arrependimento/mudança de ideia pode travar o seu reembolso em análise manual pela plataforma por até 30 dias. Seguindo os passos acima, seu dinheiro cai de volta na conta de forma automática!
        
        💬 *Dúvidas sobre como fazer? Clique no botão ao lado para falar conosco diretamente no WhatsApp (11 99425-1306).*
        """)

# Customização extra para o botão do WhatsApp não quebrar o visual OGNET
st.markdown("""
    <style>
    div[data-testid="column"] button {
        height: 50px !important;
    }
    </style>
    """, unsafe_allow_html=True)
st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Divisão Corporativa de Suporte Técnico Pós-Venda.")
