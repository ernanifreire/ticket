import streamlit as st
import PyPDF2
from openai import OpenAI
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets GPT", layout="wide")

st.title("📊 Analisador de Tickets (Motor GPT-4o)")
st.markdown("Extração de dados de SLA e Causa Raiz via OpenAI API.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Insira sua OpenAI API Key:", type="password")
    st.info("Obtenha sua chave em: platform.openai.com")

if api_key:
    # Inicializa o cliente OpenAI
    client = OpenAI(api_key=api_key)

    uploaded_files = st.file_uploader("Selecione seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                # 1. Extração de Texto do PDF
                reader = PyPDF2.PdfReader(file)
                texto_ticket = ""
                for page in reader.pages:
                    texto_ticket += page.extract_text() or ""

                # 2. Chamada para o GPT
                # Usamos o gpt-4o-mini que é rápido e barato
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um analista de dados que extrai informações de tickets de suporte. Retorne os dados em formato CSV separado por ponto e vírgula (;)."},
                        {"role": "user", "content": f"Analise este ticket e extraia: ID; Data; SLA; Problema; Causa_Raiz; Resolucao. Ticket: {texto_ticket[:12000]}"}
                    ],
                    temperature=0
                )

                # 3. Tratamento da resposta
                resultado = response.choices[0].message.content.strip()
                # Remove possíveis cabeçalhos que o GPT possa enviar
                resultado = resultado.split('\n')[-1] 
                
                colunas = resultado.split(";")
                if len(colunas) >= 5:
                    lista_dados.append(colunas[:6])
                else:
                    lista_dados.append([file.name, "Erro de formato", "-", "-", "-", "-"])

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        # --- EXIBIÇÃO ---
        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
            st.subheader("📋 Relatório Extraído")
            st.dataframe(df, use_container_width=True)

            # Exportação para Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Baixar Excel",
                data=output.getvalue(),
                file_name="relatorio_tickets_gpt.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- INSIGHTS ---
            st.divider()
            st.subheader("💡 Insights Estratégicos")
            causas = " ".join(df['Causa Raiz'].astype(str).tolist())
            
            insight_res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Com base nessas causas raízes, sugira 3 ações para reduzir o volume de tickets: {causas}"}]
            )
            st.info(insight_res.choices[0].message.content)

else:
    st.warning("Aguardando API Key da OpenAI na barra lateral.")
