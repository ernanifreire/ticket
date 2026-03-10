import streamlit as st
import PyPDF2
from groq import Groq
import pandas as pd
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Analisador de Tickets Groq", layout="wide")
st.title("📊 Analisador de Tickets (Motor Groq/Llama 3)")

with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Insira sua Groq API Key:", type="password")
    st.info("Obtenha grátis em: console.groq.com")

if api_key:
    client = Groq(api_key=api_key)

    uploaded_files = st.file_uploader("Selecione seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                # 1. Extração do PDF
                reader = PyPDF2.PdfReader(file)
                texto_ticket = "".join([page.extract_text() or "" for page in reader.pages])

                # 2. Chamada Groq (Llama 3)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um analista técnico. Extraia dados de tickets e responda APENAS com uma linha CSV usando ponto e vírgula (;).",
                        },
                        {
                            "role": "user",
                            "content": f"Extraia ID; Data; SLA; Problema; Causa_Raiz; Resolucao deste ticket: {texto_ticket[:15000]}",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0,
                )

                # 3. Tratamento
                resultado = chat_completion.choices[0].message.content.strip()
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

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio_groq.xlsx")

else:
    st.warning("Insira a API Key da Groq para começar.")
