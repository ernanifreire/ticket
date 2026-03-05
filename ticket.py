import streamlit as st
import PyPDF2
import google.generativeai as genai
from google.generativeai.types import RequestOptions
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets IA", layout="wide")

st.title("📊 Analisador Estratégico de Tickets (Versão 2026)")
st.markdown("""
Esta ferramenta processa históricos de chat (PDF), extrai dados de SLA e identifica causas raízes.
""")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave gratuita em: aistudio.google.com")
    
    st.divider()
    st.markdown("### Instruções")
    st.write("1. Insira a chave da API.")
    st.write("2. Faça upload de até 20 PDFs.")
    st.write("3. Clique em Iniciar Análise.")

# --- INICIALIZAÇÃO DA IA ---
model = None
if api_key:
    try:
        # Forçamos a configuração para usar a API v1 estável
        genai.configure(api_key=api_key)
        
        # O SEGREDO: RequestOptions força a versão 'v1' e evita o erro 404 (v1beta)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            request_options=RequestOptions(api_version='v1')
        )
        st.sidebar.success("Conectado com sucesso (API v1)")
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar: {e}")

# --- INTERFACE DE UPLOAD ---
uploaded_files = st.file_uploader("Arraste seus arquivos PDF aqui", type="pdf", accept_multiple_files=True)

if uploaded_files and model:
    if st.button("🚀 Iniciar Análise Profunda"):
        lista_dados = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, file in enumerate(uploaded_files):
            status_text.text(f"Processando: {file.name}")
            
            try:
                # 1. Extração de Texto do PDF
                reader = PyPDF2.PdfReader(file)
                texto_ticket = ""
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        texto_ticket += content

                # 2. Prompt Estruturado para Logs de Chat
                prompt = f"""
                Você é um especialista em suporte técnico. Analise o LOG DE CONVERSA abaixo.
                Ignore mensagens automáticas e identifique:
                - ID do Ticket (se houver)
                - Data de Início
                - Tempo de SLA (duração total)
                - O Problema Real relatado pelo cliente
                - A Causa Raiz (por que o problema aconteceu?)
                - A Resolução (como foi resolvido?)

                Retorne APENAS uma linha com os campos separados por ponto e vírgula (;).
                Formato: ID;Data;SLA;Problema;Causa Raiz;Resolucao

                Texto do Ticket:
                {texto_ticket[:10000]}
                """

                # 3. Chamada da IA com tratamento de erro específico
                response = model.generate_content(prompt)
                
                # Limpeza básica da resposta para evitar quebras no CSV
                resultado = response.text.replace('\n', ' ').strip()
                dados_linha = resultado.split(";")
                
                # Garante que temos o número correto de colunas
                if len(dados_linha) >= 6:
                    lista_dados.append(dados_linha[:6])
                else:
                    # Caso a IA não consiga formatar, tentamos salvar o nome do arquivo e o erro
                    lista_dados.append([file.name, "Erro", "Erro", "Formato Inválido", "N/A", "N/A"])

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("Análise Concluída!")

        # --- EXIBIÇÃO DOS RESULTADOS ---
        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
            
            st.subheader("📋 Relatório Consolidado")
            st.dataframe(df, use_container_width=True)

            # Geração do arquivo Excel para Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Tickets')
            
            st.download_button(
                label="📥 Baixar Relatório em Excel",
                data=output.getvalue(),
                file_name="analise_causa_raiz_tickets.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- INSIGHTS ESTRATÉGICOS ---
            st.divider()
            st.subheader("💡 Análise de Causa Raiz (IA)")
            causas_texto = " ".join(df['Causa Raiz'].astype(str).tolist())
            insight_prompt = f"Com base nessas causas raízes de tickets, resuma os 3 principais problemas e sugira ações para eliminá-los: {causas_texto}"
            
            try:
                insight_res = model.generate_content(insight_prompt)
                st.info(insight_res.text)
            except:
                st.write("Não foi possível gerar insights automáticos agora.")

elif not model and api_key:
    st.info("Aguardando configuração da API...")
else:
    st.warning("👈 Insira sua API Key na barra lateral para começar.")
