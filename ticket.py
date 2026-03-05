import streamlit as st
import PyPDF2
import google.generativeai as genai
import pandas as pd
import io
import os

# --- FORÇAR API ESTÁVEL (V1) ---
os.environ["GOOGLE_GENERATIVE_AI_API_VERSION"] = "v1"

st.set_page_config(page_title="Analisador de Tickets", layout="wide")
st.title("📊 Analisador Estratégico de Tickets")

with st.sidebar:
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")

if api_key:
    try:
        # Configuração com transporte REST para evitar erros de rede
        genai.configure(api_key=api_key, transport='rest')
        
        # Usamos o nome mais simples possível
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Teste de conexão real antes de começar
        model.generate_content("test", generation_config={"max_output_tokens": 1})
        st.sidebar.success("Conectado à API Estável!")
    except Exception as e:
        st.sidebar.error(f"Erro de Conexão: {e}")

    uploaded_files = st.file_uploader("Suba seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                reader = PyPDF2.PdfReader(file)
                texto = ""
                for page in reader.pages:
                    texto += page.extract_text() or ""

                # Prompt focado em extração de dados de suporte
                prompt = f"""
                Analise este ticket de suporte e retorne APENAS uma linha CSV separada por ponto e vírgula (;).
                Campos: ID; Data; SLA; Problema; Causa_Raiz; Resolucao
                Ticket: {texto[:8000]}
                """

                response = model.generate_content(prompt)
                
                # Tratamento da resposta para evitar quebras
                resultado = response.text.replace('\n', ' ').strip()
                colunas = resultado.split(";")
                
                if len(colunas) >= 5:
                    lista_dados.append(colunas[:6])
                else:
                    lista_dados.append([file.name, "Erro de formato", "-", "-", "-", "-"])

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
            st.subheader("📋 Relatório Extraído")
            st.dataframe(df, use_container_width=True)
            
            # Exportação Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio_final.xlsx")

else:
    st.warning("Insira a API Key para ativar o sistema.")
