import os
import requests
import pandas as pd
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES DA API E BASELINKER
# ==========================================
BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
API_TOKEN = os.environ.get("BASELINKER_TOKEN", "8005379-8008488-VNRWQK4RZAPBTQ56SPHT6YDWXDJBJH83WPFY4C99A0E903RNR9SWPA9VO3BAYDZJ")
ID_TABELA_VENDA_DIRETA = "19191"

def buscar_produto_baselinker(termo):
    """Varre TODOS os catálogos do BaseLinker buscando por SKU (exato/parcial) ou Nome"""
    headers = {"X-BLToken": API_TOKEN}
    termo_limpo = termo.strip().upper()
    
    try:
        # 1. Pega TODOS os catálogos/inventários cadastrados na conta
        resp_inv = requests.post(BASELINKER_API_URL, data={"method": "getInventories", "parameters": "{}"}, headers=headers).json()
        inventarios = resp_inv.get("inventories", [])
        
        for inv in inventarios:
            id_inv = inv.get("inventory_id")
            product_id = None
            
            # Tentativa A: Busca exata pelo SKU nesse catálogo
            payload_sku = {
                "method": "getInventoryProductsList",
                "parameters": json.dumps({"inventory_id": id_inv, "filter_sku": termo_limpo})
            }
            resp_sku = requests.post(BASELINKER_API_URL, data=payload_sku, headers=headers).json()
            produtos = resp_sku.get("products", {})
            
            # Tentativa B: Se não achou exato, busca pelo filtro geral (pega SKU parcial ou Nome)
            if not produtos:
                payload_name = {
                    "method": "getInventoryProductsList",
                    "parameters": json.dumps({"inventory_id": id_inv, "filter_name": termo_limpo})
                }
                resp_name = requests.post(BASELINKER_API_URL, data=payload_name, headers=headers).json()
                produtos_name = resp_name.get("products", {})
                
                # Confere se o termo bate com o SKU de algum resultado retornado
                for pid, pinfo in produtos_name.items():
                    if termo_limpo in str(pinfo.get("sku", "")).upper():
                        product_id = pid
                        break
                if not product_id and produtos_name:
                    product_id = list(produtos_name.keys())[0]
            else:
                product_id = list(produtos.keys())[0]
                
            # Se encontrou o ID do produto neste catálogo, puxa preço e estoque
            if product_id:
                payload_data = {
                    "method": "getInventoryProductsData",
                    "parameters": json.dumps({"inventory_id": id_inv, "products": [int(product_id)]})
                }
                resp_data = requests.post(BASELINKER_API_URL, data=payload_data, headers=headers).json()
                dados_prod = resp_data.get("products", {}).get(str(product_id))
                
                if dados_prod:
                    nome = dados_prod.get("text_fields", {}).get("name", "Produto sem nome")
                    sku_real = dados_prod.get("sku", termo_limpo)
                    
                    # Pega o preço da tabela Venda Direta (ou o primeiro preço disponível se não tiver nessa tabela)
                    precos = dados_prod.get("prices", {})
                    preco = precos.get(ID_TABELA_VENDA_DIRETA)
                    if preco is None and precos:
                        preco = list(precos.values())[0]
                    preco = float(preco) if preco is not None else 0.0
                    
                    estoque = sum(dados_prod.get("stock", {}).values()) if dados_prod.get("stock") else 0
                    return nome, sku_real, preco, int(estoque)
    except Exception:
        pass
    return None, None, None, None

# ==========================================
# ROTA QUE O TYPEBOT VAI ACESSAR
# ==========================================
@app.route('/consultar', methods=['POST'])
def consultar_modelo():
    dados = request.json or {}
    termo_busca = dados.get('modelo', '').strip().upper()
    
    if not termo_busca:
        return jsonify({"mensagem": "⚠️ Por favor, digite o modelo ou SKU desejado."}), 400

    try:
        # 1. TENTA BUSCAR PRIMEIRO NA PLANILHA (Excel)
        if os.path.exists("base_gaxetas.xlsx"):
            df = pd.read_excel("base_gaxetas.xlsx")
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                
            coluna_modelo = [c for c in df.columns if 'MODELO' in c or 'PRODUTO' in c or 'CODIGO' in c][0]
            colunas_sku = [c for c in df.columns if 'SKU' in c]
            nome_col_sku = colunas_sku[0] if colunas_sku else ''
            
            if nome_col_sku:
                resultado = df[(df[coluna_modelo].str.contains(termo_busca, na=False, regex=False)) | (df[nome_col_sku].str.contains(termo_busca, na=False, regex=False))]
            else:
                resultado = df[df[coluna_modelo].str.contains(termo_busca, na=False, regex=False)]
            
            if not resultado.empty:
                row = resultado.iloc[0]
                marca = row.get('MARCA', 'N/A')
                modelo_encontrado = row.get(coluna_modelo, 'N/A')
                medida_ext = row.get('MEDIDA-EXTERNA', 'N/A')
                medida_enc = row.get('MEDIDA-ENCAIXE', 'N/A')
                sku_bruto = row.get(nome_col_sku, '') if nome_col_sku else ''
                
                if sku_bruto == 'NAN' or not sku_bruto:
                    msg = f"📦 *Produto Localizado*\n\n🔹 *Marca:* {marca}\n🔹 *Modelo:* {modelo_encontrado}\n📐 *Medida Ext:* {medida_ext}\n📐 *Medida Enc:* {medida_enc}\n\n⚠️ *Preço indisponível no momento.*\nDeseja falar comigo para cotar esse item? Digite *0*."
                    return jsonify({"mensagem": msg})
                    
                skus = str(sku_bruto).split('/')
                detalhes_skus = []
                
                for s in skus:
                    sku_limpo = s.strip()
                    if not sku_limpo: continue
                    
                    nome_prod, sku_real, preco, estoque = buscar_produto_baselinker(sku_limpo)
                    if preco is not None:
                        status_estoque = f"✅ {estoque} peças" if estoque > 0 else "⏳ Sob encomenda"
                        valor_formatado = f"R$ {preco:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        txt = f"🛒 *SKU:* {sku_real}\n💰 *Preço:* {valor_formatado}\n📦 *Estoque:* {status_estoque}"
                        detalhes_skus.append(txt)
                    else:
                        detalhes_skus.append(f"🛒 *SKU:* {sku_limpo}\n⚠️ *Preço não localizado.*")
                        
                texto_skus = "\n\n".join(detalhes_skus)
                mensagem_final = f"📦 *Gaxeta Localizada!*\n\n🔹 *Marca:* {marca}\n🔹 *Modelo:* {modelo_encontrado}\n📐 *Medida Ext:* {medida_ext}\n\n{texto_skus}\n\n👉 *Quer fechar o pedido ou tirar dúvidas? Digite 0 para falar comigo.*"
                return jsonify({"mensagem": mensagem_final})

        # 2. SE NÃO ACHOU NA PLANILHA, BUSCA DIRETO EM TODOS OS CATÁLOGOS DO BASELINKER
        nome_prod, sku_real, preco, estoque = buscar_produto_baselinker(termo_busca)
        
        if preco is not None:
            status_estoque = f"✅ {estoque} peças" if estoque > 0 else "⏳ Sob encomenda"
            valor_formatado = f"R$ {preco:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            msg_bl = f"📦 *Produto Localizado*\n\n🔹 *Nome:* {nome_prod}\n🛒 *SKU:* {sku_real}\n💰 *Preço:* {valor_formatado}\n📦 *Estoque:* {status_estoque}\n\n👉 *Quer fechar o pedido ou tirar dúvidas? Digite 0 para falar comigo.*"
            return jsonify({"mensagem": msg_bl})
        
        # 3. SE NÃO ACHOU EM LUGAR NENHUM
        return jsonify({"mensagem": f"❌ Poxa, não encontrei o modelo ou SKU *{termo_busca}*.\n\nQuer falar com o Otávio para ele verificar para você? Digite *0*."})
        
    except Exception as e:
        return jsonify({"mensagem": "❌ Ocorreu um erro interno ao buscar os dados.\nDigite *0* para falar com o atendente."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
