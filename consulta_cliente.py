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
    
    if not texto_cliente.strip() and foto_upload is None:
        st.warning("Por favor, envie uma foto ou descreva seu problema antes de iniciar.")
        prosseguir = False
        
    if prosseguir:
        # 1. UPLOAD DA IMAGEM PARA O IMGBB (Se houver)
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

        # 2. ENVIA PARA O WEBHOOK DO MAKE PARA A IA ANALISAR PRIMEIRO
        payload = {
            "foto": link_imagem_final,
            "texto": texto_cliente.strip()
        }
        
        with st.spinner("🤖 O Neto está analisando seu caso... Por favor, aguarde."):
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                
                if response.status_code == 200:
                    try:
                        resposta_json = response.json()
                        resposta_ia = resposta_json.get("resposta_ia", response.text)
                    except ValueError:
                        resposta_ia = response.text
                    
                    # 3. AGORA A BUSCA INTELIGENTE NO EXCEL COMPARA COM A RESPOSTA DA IA + TEXTO DO CLIENTE
                    sku_encontrado = None
                    medida_encontrada = None
                    marca_encontrada = None
                    
                    if os.path.exists(ARQUIVO_BANCO_DADOS):
                        try:
                            df = pd.read_excel(ARQUIVO_BANCO_DADOS)
                            df['MODELO_LIMPO'] = df['MODELO'].astype(str).str.upper().str.strip()
                            
                            # Juntamos o que o cliente digitou COM o que a IA identificou na foto
                            texto_completo_analise = (texto_cliente + " " + resposta_ia).upper().strip()
                            
                            # Varre a planilha procurando se o modelo está no texto completo
                            match = df[df.apply(lambda row: row['MODELO_LIMPO'] in texto_completo_analise if row['MODELO_LIMPO'] not in ['NAN', ''] else False, axis=1)]
                            
                            if not match.empty:
                                sku_encontrado = str(match.iloc[0].get('SKU', ''))
                                medida_encontrada = str(match.iloc[0].get('MEDIDA', ''))
                                marca_encontrada = str(match.iloc[0].get('MARCA', ''))
                        except Exception:
                            pass

                    # 4. EXIBE A RESPOSTA FINAL FORMATADA NA TELA DO CLIENTE
                    st.success("Análise concluída!")
                    st.subheader("📋 Resposta do Técnico Neto:")
                    st.write(resposta_ia)
                    
                    # Se encontrou o SKU na planilha, joga o card de compra logo abaixo da resposta da IA
                    if sku_encontrado and sku_encontrado != 'nan':
                        st.markdown("---")
                        st.markdown(f"### 🎯 Produto Recomendado:")
                        st.success(f"**Código SKU:** {sku_encontrado} | **Medidas:** {medida_encontrada} ({marca_encontrada})")
                        st.markdown("👉 *Confirme se as medidas batem com a sua gaxeta antiga antes de finalizar a compra.*")
                        
                    st.balloons() 
                else:
                    st.error(f"Houve um problema no servidor. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Não foi possível conectar ao motor de IA.")

st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
