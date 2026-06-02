import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# Configuração da página do Streamlit
st.set_page_config(page_title="Técnico Virtual - OGNET Borrachas", page_icon="🚪", layout="wide")

st.title("🛠️ Painel de Testes: Agente de Instalação OGNET")
st.write("Simule aqui o atendimento ao cliente enviando fotos ou dúvidas sobre a instalação das gaxetas.")

# Configuração da API Key na Barra Lateral
st.sidebar.header("Configurações do Agente")
api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# Prompt do Sistema (Cérebro do Agente)
SYSTEM_INSTRUCTION = """
Você é o Técnico Virtual da OGNET Borrachas. Seu objetivo é ajudar clientes a instalar 
borrachas de geladeira de forma prática e educada. Se receber uma foto, analise o encaixe, 
vãos ou deformidades e forneça o passo a passo para corrigir (ex: uso de secador de cabelo, 
ajuste de dobradiças, começar a instalar pelos cantos). Seja direto e use tópicos.
"""

# Inicializa o histórico de chat no Streamlit se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], caption="Imagem enviada", width=300)

# Se a API Key não foi inserida, avisa o usuário
if not api_key:
    st.warning("⚠️ Por favor, insira sua Gemini API Key na barra lateral para começar.")
else:
    try:
        # Inicializa o cliente oficial moderno
        ai = genai.Client(api_key=api_key)

        # Área de Upload de Imagem (Simulando o cliente enviando foto no WhatsApp)
        st.sidebar.markdown("---")
        uploaded_file = st.sidebar.file_uploader("Simular envio de foto (WhatsApp)", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.sidebar.image(image, caption="Preview da foto do cliente", use_container_width=True)

        # Campo de entrada de texto do chat
        if prompt := st.chat_input("Ex: Minha borracha está com uma fresta no canto superior..."):
            
            # Mostra a mensagem do usuário no chat
            with st.chat_message("user"):
                st.markdown(prompt)
                if uploaded_file:
                    st.image(image, width=300)

            # Guarda no histórico da sessão
            user_msg = {"role": "user", "content": prompt}
            if uploaded_file:
                user_msg["image"] = image
            st.session_state.messages.append(user_msg)

            # Chamada à API do Gemini usando o SDK moderno
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🔄 *Analisando problema...*")
                
                # Prepara o conteúdo (Texto e Imagem se houver)
                conteudo_para_gemini = []
                if uploaded_file:
                    conteudo_para_gemini.append(image)
                conteudo_para_gemini.append(prompt)
                
                # Configura as instruções do sistema
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.3
                )
                
                # Executa a geração usando o modelo correto
                resposta_ia = ai.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=conteudo_para_gemini,
                    config=config
                )
                
                # Exibe a resposta final
                message_placeholder.markdown(resposta_ia.text)
                
                # Salva a resposta no histórico
                st.session_state.messages.append({"role": "assistant", "content": resposta_ia.text})
                    
    except Exception as e:
        st.error(f"❌ Erro ao inicializar ou chamar a API: {e}")
