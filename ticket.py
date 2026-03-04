import streamlit as st
import PyPDF2
import google.generativeai as genai
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets IA", layout="wide")

st.title("📊 Analisador Estratégico de Tickets")
st.markdown("""
Sobe os teus PDFs de atendimento e eu vou extrair os dados, calcular o SLA, 
identificar causas raízes e gerar uma planilha pronta para download.
""")

# --- CONFIGURAÇÃO DA IA ---
# Dica: Em produção (Streamlit Cloud), use st.secrets para a chave
api_key = st.sidebar.text_input("AIzaSyDkTKn3uiGfit05HX7QpL8mbR-0SZKUdQ8", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- UPLOAD DE ARQUIVOS ---
    uploaded_files = st.file_uploader("Selecione os 20 PDFs de tickets", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Iniciar Análise Profunda"):
            lista_dados = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, file in enumerate(uploaded_files):
                status_text.text(f"Lendo arquivo: {file.name}...")
                
                # 1. Extração de Texto do PDF
                try:
                    reader = PyPDF2.PdfReader(file)
                    texto_completo = ""
                    for page in reader.pages:
                        texto_completo += page.extract_text()

                    # 2. Prompt Estruturado para a IA
                    prompt = f"""
                    Analise o seguinte log de ticket de suporte e extraia as informações estritamente no formato JSON:
                    Campos: 
                    - id_ticket: (número ou ID)
                    - inicio: (data/hora de abertura)
                    - tmr: (tempo médio de resposta, se houver)
                    - sla_total: (tempo total de resolução)
                    - problema: (resumo do problema do cliente)
                    - causa_raiz: (o motivo real que gerou o problema)
                    - resolucao: (como foi resolvido)
                    - categoria: (ex: Bug, Dúvida, Financeiro, Técnico)

                    Texto do Ticket:
                    {texto_completo}
                    """

                    # 3. Chamada da IA
                    response = model.generate_content(prompt)
                    
                    # Limpeza simples para garantir que pegamos apenas o JSON (caso a IA mande markdown)
                    res_text = response.text.replace("```json", "").replace("```", "").strip()
                    
                    # Converter string para dicionário (Simulado aqui por praticidade, o ideal é usar json.loads)
                    # Para este MVP, vamos pedir um formato CSV simples para a IA facilitar:
                    prompt_csv = f"Extraia os dados deste ticket: {texto_completo}. Retorne APENAS uma linha CSV com: ID;Início;TMR;SLA;Problema;Causa Raiz;Resolução;Categoria. Use ';' como separador."
                    res_csv = model.generate_content(prompt_csv).text
                    
                    # Organizando os dados (Simulação de parsing rápido)
                    dados_linha = res_csv.split(";")
                    lista_dados.append(dados_linha)

                except Exception as e:
                    st.error(f"Erro ao processar {file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))

            # --- EXIBIÇÃO E DOWNLOAD ---
            st.success("✅ Análise concluída!")
            
            # Criando o DataFrame (Planilha)
            df = pd.DataFrame(lista_dados, columns=['ID', 'Início', 'TMR', 'SLA', 'Problema', 'Causa Raiz', 'Resolução', 'Categoria'])
            
            st.subheader("📋 Visualização dos Dados")
            st.dataframe(df, use_container_width=True)

            # Botão para baixar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Tickets')
            
            st.download_button(
                label="📥 Baixar Relatório em Excel",
                data=output.getvalue(),
                file_name="relatorio_tickets_ia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Insights de Causa Raiz
            st.subheader("💡 Insights Sugeridos pela IA")
            resumo_prompt = f"Com base nesses dados de causa raiz: {df['Causa Raiz'].tolist()}, quais os 3 pontos principais de melhoria?"
            insight = model.generate_content(resumo_prompt)
            st.info(insight.text)

else:
    st.warning("Por favor, insira sua API Key na barra lateral para começar.")