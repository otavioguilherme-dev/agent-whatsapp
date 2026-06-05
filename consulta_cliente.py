import streamlit as st
import requests
import json
import base64
import pandas as pd
import os
import re

# Configuração visual da página
st.set_page_config(
    page_title="Suporte Técnico Virtual - OGNET BORRACHAS",
    page_icon="⚡",
    layout="centered"
)

# --- CONFIGURAÇÕES DE INTEGRAÇÃO ---
WEBHOOK_URL = "https://hook.us2.make.com/3jdepfa2nlkipkyjj44qm2pmva1yndbi"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Nome do seu arquivo que você subiu no GitHub
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

if st.button("🚀 Iniciar Análise do Otávio Guilherme", type="primary", use_container_width=True):
    link_imagem_final = ""
    prosseguir = True
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva seu problema antes de iniciar.")
        prosseguir = False
        
    if prosseguir:
        # --- CASO 1: O CLIENTE ENVIOU UMA FOTO (CHAMA A IA + EXCEL) ---
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

            payload = {
                "foto": link_imagem_final,
                "texto": texto_cliente.strip()
            }
            
            with st.spinner("🤖 O Otávio Guilherme está analisando seu caso... Por favor, aguarde."):
                try:
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                    
                    if response.status_code == 200:
                        try:
                            resposta_json = response.json()
                            resposta_ia = resposta_json.get("resposta_ia", response.text)
                        except ValueError:
                            resposta_ia = response.text
                        
                        sku_encontrado = None
                        medida_encontrada = None
                        marca_encontrada = None
                        
                        if os.path.exists(ARQUIVO_BANCO
