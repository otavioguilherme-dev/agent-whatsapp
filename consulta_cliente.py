import streamlit as st
import requests
import json
import base64
import pandas as pd
import os
import re

# Configuração visual da página
st.set_page_config(
    page_title="Técnico IA-Virtual da OGNET BORRACHAS",
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
    st.image("https://ognetborrachas.streamlit.app/~/+/media/38265db37548b0d424994d0517a2b3ae.jpg", width=200)
except Exception:
    pass  

st.title("⚡ Especialista Técnico Virtual da OGNET BORRACHAS")
st.markdown("Seja bem-vindo ao portal de apoio e suporte da **OGNET BORRACHAS**.")
st.divider()

st.subheader("📋 Envie os dados do produto que voce deseja comprar ou obter suporte")

foto_upload = st.file_uploader("📸 1. Selecione ou tire uma foto nítida (da etiqueta com o modelo comercial ou do problema que esta ocorrendo na sua borracha):", type=["png", "jpg", "jpeg"])

if foto_upload is not None:
    st.image(foto_upload, caption="Sua foto carregada.", width=300)

texto_cliente = st.text_area(
    "✍️ 2. Descreva o problema que esta ocorrendo com a sua borracha/instalação ou ou digite o modelo da geladeira/freezer que voce deseja comprar:",
    placeholder="Ex: Minha geladeira é o modelo BRM44B, qual o modelo devo comprar? ou troquei a borracha mas o ima é fraco",
    key="relato_unico"
)

def limpar_resposta_ia(texto_bruto):
    if not isinstance(texto_bruto, str):
        return ""
    
    texto = texto_bruto.strip()
    
    # 1. Remove qualquer combinação de sujeira de JSON/Result duplicado no início
    # Remove {"resposta_ia": ou {"result":
    texto = re.sub(r'^\{\s*"(resposta_ia|result)"\s*:\s*"', '', texto)
    # Remove o segundo nível se o Make duplicou: {"result": ou {"resposta_ia":
    texto = re.sub(r'^\{\s*"(resposta_ia|result)"\s*:\s*"', '', texto)
    
    # 2. Corta metadados residuais conhecidos que o Make joga no fim do buffer
    for delimitador in ['","thoughtSignature"', '"thoughtSignature"', '","role"', '"finishReason"', '","candidates"', '"candidates"']:
        if delimitador in texto:
            texto = texto.split(delimitador, 1)[0]
            
    # 3. Restaura formatações e quebras de linha textuais literais
    texto = texto.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '    ')
    
    # 4. Faxina final nas pontas para arrancar aspas e chaves órfãs
    texto = texto.strip()
    while texto.endswith('}') or texto.endswith('"') or texto.endswith(']'):
        if texto.endswith('}'): texto = texto[:-1].strip()
        if texto.endswith('"'): texto = texto[:-1].strip()
        if texto.endswith(']'): texto = texto[:-1].strip()
        
    return texto.strip()


if st.button("🚀 Iniciar Análise do Especialista OGNET", type="primary", use_container_width=True):
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
            
            with st.spinner("🤖 O especialista OGNET está analisando seu caso... Por favor, aguarde."):
                try:
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        resposta_ia = limpar_resposta_ia(response.text)
                        
                        sku_encontrado = None
                        medida_encontrada = None
                        marca_encontrada = None
                        
                        if os.path.exists(ARQUIVO_BANCO_DADOS):
                            try:
                                df = pd.read_excel(ARQUIVO_BANCO_DADOS)
                                df = df.dropna(subset=['MODELO'])
                                texto_completo = (texto_cliente + " " + resposta_ia).upper()
                                df['MODELO_BUSCA'] = df['MODELO'].astype(str).str.upper().str.strip()
                                
                                match = pd.DataFrame()
                                for idx, row in df.iterrows():
                                    mod = row['MODELO_BUSCA']
                                    if len(mod) < 2 or mod in ['NAN', '']: continue
                                    if mod in ['UM', 'DE', 'A', 'O', 'E', 'PARA', 'COM', 'POR', 'TIPO', 'EM', 'S SUA']: continue
                                    if re.search(r'\b' + re.escape(mod) + r'\b', texto_completo):
                                        match = df.loc[[idx]]
                                        break

                                if not match.empty:
                                    sku_encontrado = str(match.iloc[0].get('SKU', ''))
                                    medida_encontrada = str(match.iloc[0].get('MEDIDA', ''))
                                    marca_encontrada = str(match.iloc[0].get('MARCA', ''))
                            except Exception:
                                pass

                        st.success("Análise concluída!")
                        st.subheader("📋 Resposta do Especialista OGNET:")
                        st.markdown(resposta_ia)
                        
                        if sku_encontrado and sku_encontrado != 'nan' and sku_encontrado != 'None':
                            st.markdown("---")
                            st.markdown(f"### 🎯 Produto Recomendado:")
                            st.success(f"**Código SKU:** {sku_encontrado} | **Medidas:** {medida_encontrada} ({marca_encontrada})")
                        st.balloons()
                    else:
                        st.error(f"Houve um problema no servidor de IA. (Código: {response.status_code})")
                except requests.exceptions.RequestException:
                    st.error("Não foi possível conectar ao motor de IA.")
                    
        # --- CASO 2: O CLIENTE APENAS DIGITOU O TEXTO (SUPORTE TÉCNICO DIRETO) ---
        else:
            sku_encontrado = None
            medida_encontrada = None
            marca_encontrada = None
            texto_busca_cliente = texto_cliente.upper().strip()
            
            if os.path.exists(ARQUIVO_BANCO_DADOS):
                with st.spinner("🔍 Verificando se é uma consulta de modelo..."):
                    try:
                        df = pd.read_excel(ARQUIVO_BANCO_DADOS)
                        df = df.dropna(subset=['MODELO'])
                        df['MODELO_BUSCA'] = df['MODELO'].astype(str).str.upper().str.strip()
                        
                        match = pd.DataFrame()
                        for idx, row in df.iterrows():
                            mod = row['MODELO_BUSCA']
                            if len(mod) < 2 or mod in ['NAN', '']: continue
                            if mod in texto_busca_cliente:
                                match = df.loc[[idx]]
                                break
                                
                        if not match.empty:
                            sku_encontrado = str(match.iloc[0].get('SKU', ''))
                            medida_encontrada = str(match.iloc[0].get('MEDIDA', ''))
                            marca_encontrada = str(match.iloc[0].get('MARCA', ''))
                    except Exception:
                        pass
            
            if sku_encontrado and sku_encontrado != 'nan' and sku_encontrado != 'None':
                st.success("Busca concluída!")
                st.subheader("📋 Resposta do Especialista OGNET:")
                st.write(f"Olá! Localizei o modelo **{texto_cliente.strip()}** diretamente em nosso catálogo de gaxetas.")
                st.markdown("---")
                st.markdown(f"### 🎯 Produto Recomendado:")
                st.success(f"**Código SKU:** {sku_encontrado} | **Medidas:** {medida_encontrada} ({marca_encontrada})")
                st.balloons()
                
            else:
                payload = {
                    "foto": "sem_foto",
                    "texto": texto_cliente.strip()
                }
                
                with st.spinner("🤖 Encaminhando para o Especialista OGNET... Por favor, aguarde."):
                    try:
                        headers = {"Content-Type": "application/json"}
                        response_ia_texto = requests.post(WEBHOOK_URL, json=payload, headers=headers)
                        
                        if response_ia_texto.status_code == 200:
                            resposta_ia = limpar_resposta_ia(response_ia_texto.text)
                            
                            espaco_resposta = st.empty()
                            with espaco_resposta.container():
                                st.success("Análise concluída!")
                                st.subheader("📋 Resposta do Especialista Otávio Guilherme - OGNET BORRACHAS:")
                                st.markdown(resposta_ia)
                        else:
                            st.error(f"Houve um problema no servidor de suporte. (Código: {response_ia_texto.status_code})")
                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao motor de IA para suporte técnico.")

# Elementos estáticos do rodapé
st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
