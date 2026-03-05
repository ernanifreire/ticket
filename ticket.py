import streamlit as st
import PyPDF2
import google.generativeai as genai
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets", layout="wide")

st.title("📊 Analisador Estratégico de Tickets")
st.markdown("Extraia dados de logs de chat (PDF) e identifique causas raízes automaticamente.")

# --- CONFIGURAÇÃO DA API (BARRA LATERAL) ---
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")
    
    st.divider()
    st.markdown("### Como usar:")
    st.write("1. Insira a chave da API acima.")
    st.write("2. Arraste os arquivos PDF de suporte.")
    st.write("3. Clique em 'Processar' e baixe o Excel.")

# --- LÓGICA DE PROCESSAMENTO ---
if api_key:
    # Configuração Global da API
    genai.configure(api_key=api_key)
    
    # Seleção do Modelo (O Flash é ideal para extração de dados por ser rápido)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro ao inicializar o modelo: {e}")

    # Upload de múltiplos arquivos
    uploaded_files = st.file_uploader("Selecione seus PDFs de ticket", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Iniciar Análise Profunda"):
            lista_dados = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, file in enumerate(uploaded_files):
                status_text.text(f"Lendo: {file.name}")
                
                try:
                    # 1. Extração de Texto do PDF
                    reader = PyPDF2.PdfReader(file)
                    texto_ticket = ""
                    for page in reader.pages:
                        texto_ticket += page.extract_text() or ""

                    # 2. Prompt Estruturado
                    # Pedimos para a IA retornar os dados separados por ";" para facilitar o split
                    prompt = f"""
                    Analise este histórico de ticket de suporte e extraia as informações abaixo.
                    Retorne APENAS uma linha com os campos separados por ponto e vírgula (;).
                    Campos: ID_Ticket; Data_Inicio; Tempo_SLA; Problema_Relatado; Causa_Raiz; Resolucao_Final

                    Texto do Ticket:
                    {texto_ticket[:10000]}
                    """

                    # 3. Chamada da IA
                    response = model.generate_content(prompt)
                    
                    # Limpeza e Parsing do Resultado
                    linha_bruta = response.text.replace('\n', ' ').strip()
                    colunas = linha_bruta.split(";")
                    
                    # Se a IA retornou o número certo de colunas, adicionamos à lista
                    if len(colunas) >= 6:
                        lista_dados.append(colunas[:6])
                    else:
                        # Fallback caso a IA falhe na formatação
                        lista_dados.append([file.name, "Erro de Formato", "-", "-", "-", "-"])

                except Exception as e:
                    st.error(f"Erro ao processar {file.name}: {e}")
                
                # Atualiza barra de progresso
                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("Análise Concluída com Sucesso!")

            # --- EXIBIÇÃO E EXPORTAÇÃO ---
            if lista_dados:
                df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
                
                st.subheader("📋 Relatório Extraído")
                st.dataframe(df, use_container_width=True)

                # Criar arquivo Excel em memória
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Análise de Tickets')
                
                st.download_button(
                    label="📥 Baixar Relatório Completo (Excel)",
                    data=output.getvalue(),
                    file_name="relatorio_tickets_suporte.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # --- ANÁLISE DE CAUSA RAIZ AGREGADA ---
                st.divider()
                st.subheader("💡 Insights de Causa Raiz")
                
                # Juntamos todas as causas raízes para um resumo final
                todas_causas = " ".join(df['Causa Raiz'].astype(str).tolist())
                insight_prompt = f"Com base nessas causas raízes de vários tickets, identifique os 3 problemas mais frequentes e sugira como evitá-los: {todas_causas}"
                
                try:
                    resumo = model.generate_content(insight_prompt)
                    st.info(resumo.text)
                except:
                    st.warning("Não foi possível gerar o resumo de insights agora.")

else:
    st.warning("Por favor, insira sua API Key na barra lateral para começar.")
