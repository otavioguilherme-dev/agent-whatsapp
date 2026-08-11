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

def buscar_produto_baselinker(sku):
    headers = {"X-BLToken": API_TOKEN}
    try:
        resp_inv = requests.post(BASELINKER_API_URL, data={"method": "getInventories", "parameters": "{}"}, headers=headers).json()
        id_inv = resp_inv.get("inventories", [])[0].get("inventory_id")
        
        payload_prod = {"method": "getInventoryProductsList", "parameters": json.dumps({"inventory_id": id_inv, "filter_sku": sku.strip()})}
        resp_prod = requests.post(BASELINKER_API_URL, data=payload_prod, headers=headers).json()
        produtos = resp_prod.get("products", {})
        
        if not produtos: return None, None
        
        product_id = list(produtos.keys())[0]
        payload_data = {"method": "getInventoryProductsData", "parameters": json.dumps({"inventory_id": id_inv, "products": [int(product_id)]})}
        resp_data = requests.post(BASELINKER_API_URL, data=payload_data, headers=headers).json()
        
        dados_prod = resp_data.get("products", {}).get(str(product_id))
        if dados_prod:
            preco = dados_prod.get("prices", {}).get(ID_TABELA_VENDA_DIRETA, 0.0)
            estoque = sum(dados_prod.get("stock", {}).values()) if dados_prod.get("stock") else 0
            return float(preco), int(estoque)
    except:
        pass
    return None, None

# ==========================================
# ROTA QUE O TYPEBOT VAI ACESSAR
# ==========================================
@app.route('/consultar', methods=['POST'])
def consultar_modelo():
    dados = request.json
    modelo_busca = dados.get('modelo', '').strip().upper()
    
    if not modelo_busca:
        return jsonify({"mensagem": "⚠️ Por favor, digite o modelo (Ex: BRM44)."}), 400

    try:
        # O arquivo base_gaxetas.xlsx deverá estar na mesma pasta deste código no servidor
        df = pd.read_excel("base_gaxetas.xlsx")
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
        # Filtra pelo modelo
        coluna_modelo = [c for c in df.columns if 'MODELO' in c or 'PRODUTO' in c or 'CODIGO' in c][0]
        resultado = df[df[coluna_modelo].str.contains(modelo_busca, na=False)]
        
        if resultado.empty:
            return jsonify({"mensagem": f"❌ Poxa, não encontrei o modelo *{modelo_busca}* na nossa base.\n\nQuer falar com o Otávio para ele verificar para você? Digite *0*."})
        
        # Pega o primeiro resultado da planilha
        row = resultado.iloc[0]
        marca = row.get('MARCA', 'N/A')
        modelo_encontrado = row.get(coluna_modelo, 'N/A')
        medida_ext = row.get('MEDIDA-EXTERNA', 'N/A')
        medida_enc = row.get('MEDIDA-ENCAIXE', 'N/A')
        sku_bruto = row.get('SKU', '')
        
        if sku_bruto == 'NAN' or not sku_bruto:
            msg = f"📦 *Produto Localizado*\n\n🔹 *Marca:* {marca}\n🔹 *Modelo:* {modelo_encontrado}\n📐 *Medida Ext:* {medida_ext}\n📐 *Medida Enc:* {medida_enc}\n\n⚠️ *Preço indisponível no momento.*\nDeseja falar comigo para cotar esse item? Digite *0*."
            return jsonify({"mensagem": msg})
            
        # Divide SKUs (ex: 036014 / 036013) e busca os preços
        skus = str(sku_bruto).split('/')
        detalhes_skus = []
        
        for s in skus:
            sku_limpo = s.strip()
            if not sku_limpo: continue
            
            preco, estoque = buscar_produto_baselinker(sku_limpo)
            if preco is not None:
                status_estoque = f"✅ {estoque} peças" if estoque > 0 else "⏳ Sob encomenda"
                # Formatação bonitinha com R$ e vírgula
                valor_formatado = f"R$ {preco:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                txt = f"🛒 *SKU:* {sku_limpo}\n💰 *Preço:* {valor_formatado}\n📦 *Estoque:* {status_estoque}"
                detalhes_skus.append(txt)
            else:
                detalhes_skus.append(f"🛒 *SKU:* {sku_limpo}\n⚠️ *Preço não localizado.*")
                
        texto_skus = "\n\n".join(detalhes_skus)
        
        # Monta a resposta final que vai para o WhatsApp do cliente
        mensagem_final = f"📦 *Produto Localizado!*\n\n🔹 *Marca:* {marca}\n🔹 *Modelo:* {modelo_encontrado}\n📐 *Medida Ext:* {medida_ext}\n\n{texto_skus}\n\n👉 *Quer fechar o pedido ou tirar dúvidas? Digite 0 para falar comigo.*"
        
        # Devolve a mensagem empacotada em JSON para o Typebot ler
        return jsonify({"mensagem": mensagem_final})
        
    except Exception as e:
        return jsonify({"mensagem": "❌ Ocorreu um erro interno ao buscar os dados.\nDigite *0* para falar com o atendente."}), 500

if __name__ == '__main__':
    # Roda o servidor na porta correta
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
