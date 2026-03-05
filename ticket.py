import streamlit as st
import PyPDF2
import google.generativeai as genai
import pandas as pd
import io

st.set_page_config(page_title="Analisador de Tickets", layout="wide")

st.title("📊 Analisador de Tickets (Versão Estável 2026)")

# --- CONFIGURAÇÃO DA API ---
# Usando st.sidebar para organizar
with st.sidebar:
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")

if api_key:
    try:
        # FORÇANDO A API V1 (ESTÁVEL) E O TRANSPORTE REST
        genai.configure(api_key=api_key, transport='rest')
        
        # Testando o modelo mais provável em 2026
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # BOTÃO DE DIAGNÓSTICO (Caso o erro persista)
        if st.button("🔍 Testar Conexão/Modelos"):
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            st.write("Modelos disponíveis na sua conta:")
            st.code(models)

    except Exception as e:
        st.error(f"Erro na configuração: {e}")

    # --- UPLOAD E PROCESSAMENTO ---
    uploaded_files = st.file_uploader("Suba seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                # Extrair texto do PDF
                reader = PyPDF2.PdfReader(file)
                texto = "".join([page.extract_text() for page in reader.pages])

                # Prompt simplificado para evitar erros de parsing
                prompt = f"""
                Analise este ticket e retorne APENAS uma linha com os campos separados por ponto e vírgula (;).
                Campos: ID; Data; SLA; Problema; Causa Raiz; Resolução
                Ticket: {texto[:5000]} 
                """
                # (Limitamos a 5000 caracteres para não estourar o limite de envio inicial)

                response = model.generate_content(prompt)
                
                # Tratamento da resposta
                linha = response.text.strip().split(";")
                if len(linha) >= 5:
                    lista_dados.append(linha)
                else:
                    lista_dados.append([file.name, "Erro formatacao", "-", "-", "-", "-"])

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
            st.subheader("📋 Resultado")
            st.dataframe(df)
            
            # Download Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio.xlsx")
else:
    st.warning("Aguardando API Key...")
