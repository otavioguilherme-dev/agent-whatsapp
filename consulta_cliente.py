import streamlit as st
import requests
import json
import base64
import pandas as pd
import os

# Configuração visual da página
st.set_page_config(
    page_title="Suporte Técnico Virtual - OGNET BORRACHAS",
    page_icon="⚡",
    layout="centered"
)

# --- CONFIGURAÇÕES DE INTEGRAÇÃO ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Nome do seu arquivo que você subiu no GitHub (ajuste o nome se for diferente)
ARQUIVO_BANCO_DADOS = "base_gaxetas.xlsx" 

# Estilização para esconder menus padrões
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

try:
    st.image("https://ognetnauticos.com.br/wp-content/uploads/2024/logo.png", width=200)
except Exception:
    pass  

st.title("⚡ Assistente Técnico Virtual")
st.markdown("Seja bem-vindo ao portal de suporte da **OGNET BORRACHAS**.")
st.divider()

st.subheader("📋 Envie os dados do seu produto")

foto_upload = st.file_uploader("📸 1. Selecione ou tire uma foto nítida (da etiqueta ou do problema):", type=["png", "jpg", "jpeg"])

if foto_upload is not None:
    st.image(foto_upload, caption="Sua foto carregada.", width=300)

texto_cliente = st.text_area(
    "✍️ 2. Descreva o que você precisa ou digite o modelo da geladeira:",
    placeholder="Ex: Minha geladeira é o modelo BRM44B, qual o SKU?",
    key="relato_unico"
)

if st.button("🚀 Iniciar Análise do Neto", type="primary", use_container_width=True):
    link_imagem_final = ""
    prosseguir = True
    
    # Variáveis técnicas que vamos buscar no Excel local
    sku_encontrado = "Não localizado na busca automática"
    medida_encontrada = "Não localizada na busca automática"
    marca_encontrada = ""
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva seu problema antes de iniciar.")
        prosseguir = False
        
    if prosseguir:
   # --- BUSCA AUTOMÁTICA INTELIGENTE NO EXCEL DO GITHUB ---
        if os.path.exists(ARQUIVO_BANCO_DADOS) and texto_cliente.strip():
            try:
                df = pd.read_excel(ARQUIVO_BANCO_DADOS)
                texto_busca = texto_cliente.upper().strip()
                
                # Criamos colunas limpas para comparação
                df['MODELO_LIMPO'] = df['MODELO'].astype(str).str.upper().str.strip()
                
                # MÁGICA DO MATCH: Varre a planilha linha por linha. 
                # Se o MODELO da linha (ex: "VB40") estiver dentro do texto grande, dá MATCH!
                match = df[df.apply(lambda row: row['MODELO_LIMPO'] in texto_busca if row['MODELO_LIMPO'] not in ['NAN', ''] else False, axis=1)]
                
                # Se não achou de primeira, tenta quebrar o texto por palavras (garantia extra)
                if match.empty:
                    palavras_busca = texto_busca.split()
                    match = df[df['MODELO_LIMPO'].isin(palavras_busca)]

                if not match.empty:
                    # Captura os dados exatos da planilha
                    sku_encontrado = str(match.iloc[0].get('SKU', 'Não informado'))
                    medida_encontrada = str(match.iloc[0].get('MEDIDA', 'Não informada'))
                    marca_encontrada = str(match.iloc[0].get('MARCA', ''))
            except Exception as e:
                pass # Evita quebrar a tela se houver erro técnico

        # --- UPLOAD DA IMAGEM PARA O IMGBB ---
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
                except Exception:
                    pass

        # --- MONTAGEM DO PACOTE COMPLETO PARA O MAKE ---
        payload = {
            "foto": link_imagem_final,
            "texto": texto_cliente.strip(),
            "sku_tabela": sku_encontrado,
            "medida_tabela": medida_encontrada,
            "marca_tabela": marca_encontrada
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
