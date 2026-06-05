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

st.subheader("📋 Envie os dados do seu product")

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
                        
                        if os.path.exists(ARQUIVO_BANCO_DADOS):
                            try:
                                df = pd.read_excel(ARQUIVO_BANCO_DADOS)
                                df = df.dropna(subset=['MODELO'])
                                
                                texto_processar = resposta_ia
                                if '"RESPOSTA_IA":' in resposta_ia:
                                    try:
                                        dados_json = json.loads(resposta_ia)
                                        texto_processar = dados_json.get("RESPOSTA_IA", resposta_ia)
                                    except Exception:
                                        texto_processar = resposta_ia.replace('{"RESPOSTA_IA":', '').replace('}', '')
                                
                                texto_completo = (texto_cliente + " " + texto_processar).upper()
                                df['MODELO_BUSCA'] = df['MODELO'].astype(str).str.upper().str.strip()
                                
                                match = pd.DataFrame()
                                for idx, row in df.iterrows():
                                    mod = row['MODELO_BUSCA']
                                    if len(mod) < 2 or mod in ['NAN', '']: continue
                                    if mod in ['UM', 'DE', 'A', 'O', 'E', 'PARA', 'COM', 'POR', 'TIPO', 'EM', 'S SUA']: continue
                                    if re.search(r'\b' + re.escape(mod) + r'\b', texto_completo):
                                        match = df.loc[[idx]]
                                        break
                                
                                if match.empty:
                                    for idx, row in df.iterrows():
                                        mod = row['MODELO_BUSCA']
                                        if len(mod) < 3 or mod in ['NAN', '']: continue
                                        if mod in texto_completo and ("MODELO" in texto_completo or "TRATA-SE" in texto_completo):
                                            if mod not in "REFRIGERAÇÃO" and mod not in "EXPOSITOR":
                                                match = df.loc[[idx]]
                                                break

                                if not match.empty:
                                    sku_encontrado = str(match.iloc[0].get('SKU', ''))
                                    medida_encontrada = str(match.iloc[0].get('MEDIDA', ''))
                                    marca_encontrada = str(match.iloc[0].get('MARCA', ''))
                            except Exception as e:
                                st.error(f"Erro ao processar busca: {e}")

                        # Limpeza de segurança para rota com Foto
                        if isinstance(resposta_ia, str):
                            for delimitador in ['","thoughtSignature"', '"thoughtSignature"', '","role"', '"finishReason"']:
                                if delimitador in resposta_ia:
                                    resposta_ia = resposta_ia.split(delimitador, 1)[0]
                            resposta_ia = resposta_ia.replace('\\n', '\n').replace('\\"', '"').strip()
                            if resposta_ia.startswith('"'): resposta_ia = resposta_ia[1:]
                            if resposta_ia.endswith('"'): resposta_ia = resposta_ia[:-1]

                        st.success("Análise concluída!")
                        st.subheader("📋 Resposta do Especialista Otávio Guilherme:")
                        st.markdown(resposta_ia)
                        
                        if sku_encontrado and sku_encontrado != 'nan' and sku_encontrado != 'None':
                            st.markdown("---")
                            st.markdown(f"### 🎯 Produto Recomendado:")
                            st.success(f"**Código SKU:** {sku_encontrado} | **Medidas:** {medida_encontrada} ({marca_encontrada})")
                            st.markdown("👉 *Confirme se as medidas batem com a sua gaxeta antiga antes de finalizar a compra.*")
                        else:
                            st.info("ℹ️ Modelo identificado na imagem, mas não localizado com precisão no arquivo Excel local.")
                        st.balloons()
                    else:
                        st.error(f"Houve um problema no servidor de IA. (Código: {response.status_code})")
                except requests.exceptions.RequestException:
                    st.error("Não foi possível conectar ao motor de IA.")
                    
        # --- CASO 2: O CLIENTE APENAS DIGITOU O TEXTO (SUPORTE TÉCNICO DIRETOR) ---
        else:
            sku_encontrado = None
            medida_encontrada = None
            marca_encontrada = None
            texto_busca_cliente = texto_cliente.upper().strip()
            
            # Passo A: Tenta uma busca rápida por modelo no Excel
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
            
            # Passo B: Se achou o SKU direto pelo modelo digitado
            if sku_encontrado and sku_encontrado != 'nan' and sku_encontrado != 'None':
                st.success("Busca concluída!")
                st.subheader("📋 Resposta do Especialista Otávio Guilherme:")
                st.write(f"Olá! Localizei o modelo **{texto_cliente.strip()}** diretamente em nosso catálogo de gaxetas.")
                st.markdown("---")
                st.markdown(f"### 🎯 Produto Recomendado:")
                st.success(f"**Código SKU:** {sku_encontrado} | **Medidas:** {medida_encontrada} ({marca_encontrada})")
                st.markdown("👉 *Confirme se as medidas batem com a sua gaxeta antiga antes de finalizar a compra.*")
                st.balloons()
                
            # Passo C: SE NÃO ACHOU SKU, PLANILHA FALHOU -> CHAMA A IA PARA SUPORTE TÉCNICO!
          if response.status_code == 200:
                            resposta_ia = ""
                            try:
                                resposta_json = response.json()
                                resposta_ia = resposta_json.get("resposta_ia", response.text)
                            except Exception:
                                resposta_ia = response.text
                            
                            # Tratamento para limpar strings e remover metadados (JSON bruto do Gemini)
                            if isinstance(resposta_ia, str):
                                if '"result":' in resposta_ia:
                                    try:
                                        dados_internos = json.loads(resposta_ia.strip())
                                        resposta_ia = dados_internos.get("result", resposta_ia)
                                    except Exception:
                                        if '"result":"' in resposta_ia:
                                            resposta_ia = resposta_ia.split('"result":"', 1)[1]
                                
                                # TRAVA ANTI-DUPLICAÇÃO: 
                                # Se a resposta contiver a introdução do Otávio repetida, corta na primeira ocorrência
                                marcador_repeticao = "Olá! Aqui é o Otávio Guilherme"
                                if resposta_ia.count(marcador_repeticao) > 1:
                                    # Separa pelo marcador e reconstrói apenas com a primeira parte do bloco
                                    partes = resposta_ia.split(marcador_repeticao)
                                    resposta_ia = marcador_repeticao + partes[1]

                                # Guilhotina de Metadados: Elimina chaves residuais de tokens e logs da API
                                for delimitador in ['","thoughtSignature"', '"thoughtSignature"', '","role"', '"finishReason"']:
                                    if delimitador in resposta_ia:
                                        resposta_ia = resposta_ia.split(delimitador, 1)[0]
                                
                                # Formatação correta das quebras de linha e aspas para Markdown
                                resposta_ia = resposta_ia.replace('\\n', '\n')
                                resposta_ia = resposta_ia.replace('\\"', '"')
                                resposta_ia = resposta_ia.strip()
                                
                                if resposta_ia.startswith('"'): resposta_ia = resposta_ia[1:]
                                if resposta_ia.endswith('"'): resposta_ia = resposta_ia[:-1]
                            
                            # Desenha a resposta estática limpa
                            espaco_resposta = st.empty()
                            with espaco_resposta.container():
                                st.success("Análise concluída!")
                                st.subheader("📋 Resposta do Especialista Otávio Guilherme:")
                                st.markdown(resposta_ia)
                                
                        else:
                            st.error(f"Houve uma oscilação no servidor de suporte. (Código: {response.status_code})")
                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao motor de IA para suporte técnico.")

# Elementos estáticos do rodapé (Totalmente isolados fora das condições do botão)
st.divider()
st.caption("© 2026 OGNET BORRACHAS - Todos os direitos reservados.")
