import streamlit as st
import PyPDF2
from groq import Groq
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Estratégica de Suporte", layout="wide")
st.title("📊 Dashboard de Análise de Tickets e Causa Raiz")
st.markdown("Transforme logs de chat em inteligência acionável para produto e operação.")

# --- CONFIGURAÇÃO DA API (BARRA LATERAL) ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("Insira sua Groq API Key:", type="password")
    
    st.divider()
    st.markdown("### Instruções:")
    st.write("1. Insira a chave da API (grátis em: console.groq.com).")
    st.write("2. Faça upload de até 20 PDFs de histórico de chat.")
    st.write("3. Clique em '🚀 Processar' para gerar a dashboard e relatório.")
    st.write("4. Baixe o Excel completo com todos os dados extraídos.")

# --- FUNÇÃO DE CHAMADA À API (GROQ/LLAMA 3) ---
def chamar_ia(api_key, system_prompt, user_content):
    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.1, # Temperatura baixa para maior consistência
    )
    return chat_completion.choices[0].message.content.strip()

# --- LÓGICA DO APP ---
if api_key:
    uploaded_files = st.file_uploader("Selecione seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("🚀 Iniciar Análise Profunda"):
            # Limitamos a 20 arquivos
            if len(uploaded_files) > 20:
                uploaded_files = uploaded_files[:20]
                st.warning("Limitado aos primeiros 20 arquivos para manter a estabilidade.")

            lista_dados = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, file in enumerate(uploaded_files):
                status_text.text(f"Processando ticket: {file.name}")
                
                try:
                    # 1. Extração do PDF
                    reader = PyPDF2.PdfReader(file)
                    texto_completo = "".join([page.extract_text() or "" for page in reader.pages])

                    # 2. Prompt Estratégico (O "Encorpamento")
                    system_prompt = """
                    Você é um analista de dados especialista em suporte ao cliente. Analise logs de chat e extraia informações detalhadas.
                    Sua resposta deve ser APENAS uma linha CSV usando ponto e vírgula (;).
                    Use N/A para campos não encontrados.
                    Campos: 
                    1. ID_Ticket: (ou nome do arquivo)
                    2. Data_Inicio: (data/hora de abertura)
                    3. Data_Termino: (data/hora do fechamento)
                    4. Tempo_Atendimento_Minutos: (duração total da conversa em minutos)
                    5. Problema_Relatado: (resumo da dor do cliente)
                    6. Causa_Raiz: (o motivo real que gerou o problema)
                    7. Categoria: (Bug, Dúvida, Financeiro, Técnico, etc.)
                    8. Solucao_Aplicada: (como foi resolvido)
                    9. Qualidade_Atendimento: (avaliação de 1-5 estrelas, baseada no tom da conversa e resolução)
                    """

                    user_content = f"Analise o seguinte log de chat técnico e extraia as informações estritamente no formato CSV. Texto: {texto_completo[:15000]}"

                    # 3. Chamada da IA
                    resultado_ia = chamar_ia(api_key, system_prompt, user_content)
                    
                    # 4. Tratamento dos dados
                    # Limpamos possíveis aspas extras ou quebras que o Llama 3 às vezes manda
                    resultado_ia = resultado_ia.replace('"', '').replace('\n', ' ').strip()
                    colunas = resultado_ia.split(";")
                    
                    # Garantimos que temos o número certo de colunas
                    if len(colunas) >= 8:
                        lista_dados.append(colunas[:9]) # Pegamos até Qualidade_Atendimento
                    else:
                        st.error(f"Erro de formato na IA para o arquivo {file.name}. Resposta: {resultado_ia}")
                        # Fallback simples
                        lista_dados.append([file.name, "Erro", "Erro", "0", "Erro Formato", "Erro Formato", "Erro", "N/A", "0"])

                except Exception as e:
                    st.error(f"Erro no arquivo {file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("Análise Concluída!")

            # --- CONSOLIDAÇÃO E DASHBOARD ---
            if lista_dados:
                st.divider()
                
                # Criando o DataFrame
                df = pd.DataFrame(lista_dados, columns=[
                    'ID', 'Início', 'Término', 'Duração (Min)', 
                    'Problema', 'Causa Raiz', 'Categoria', 'Solução', 'Qualidade (1-5)'
                ])
                
                # Conversões de tipo para estatística
                df['Duração (Min)'] = pd.to_numeric(df['Duração (Min)'], errors='coerce').fillna(0).astype(int)
                df['Qualidade (1-5)'] = pd.to_numeric(df['Qualidade (1-5)'], errors='coerce').fillna(0).astype(int)

                # Exportação Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.sidebar.download_button("📥 Baixar Excel Completo", output.getvalue(), "relatorio_tickets.xlsx")

                # --- DASHBOARD VISUAL (Plotly) ---
                st.header("📊 Dashboard Interativa")
                
                c1, c2, c3 = st.columns(3)
                
                # KPI: Tempo Médio de Atendimento
                tma_medio = df['Duração (Min)'].mean()
                c1.metric("Tempo Médio de Atendimento (TMA)", f"{tma_medio:.1f} min")
                
                # KPI: Qualidade Média
                qual_media = df['Qualidade (1-5)'].mean()
                c2.metric("Qualidade Média do Atendimento", f"{qual_media:.1f} ⭐")

                # Gráfico 1: Categorias Mais Frequentes
                st.subheader("📋 Top Categorias de Tickets")
                df_cat = df['Categoria'].value_with_counts().reset_index()
                df_cat.columns = ['Categoria', 'Contagem']
                fig_cat = px.bar(df_cat, x='Contagem', y='Categoria', orientation='h', text='Contagem')
                st.plotly_chart(fig_cat, use_container_width=True)

                # --- ANÁLISE DE CAUSA RAIZ E RECOMENDAÇÕES (O "Relatório de Ataque") ---
                st.divider()
                st.header("💡 Relatório de Causa Raiz e Plano de Ataque (IA)")
                
                # Juntamos as causas raízes e as categorias para análise agregada
                todas_causas = " | ".join(df['Causa Raiz'].astype(str).tolist())
                todas_categorias = " | ".join(df['Categoria'].astype(str).tolist())
                
                system_insight_prompt = "Você é um analista estratégico de operações de suporte. Analise os dados consolidados de múltiplos tickets e gere um relatório de ataque."
                user_insight_content = f"""
                Analise os seguintes dados agregados de causa raiz e categoria de 20 tickets de suporte.
                Retorne um relatório estruturado em Markdown com as seguintes seções:
                1. **Top 5 Problemas Recorrentes e Suas Causas Raízes:** Identifique os 5 padrões mais comuns.
                2. **Recomendações Práticas para Produto/Engenharia:** Sugira mudanças concretas no produto que eliminariam esses tickets.
                3. **Recomendações Práticas para Operação/Treinamento de Suporte:** Sugira melhorias na forma como o atendimento é feito.

                Dados de Causa Raiz: {todas_causas[:20000]}
                Dados de Categoria: {todas_categorias[:10000]}
                """
                
                try:
                    insight_res = chamar_ia(api_key, system_insight_prompt, user_insight_content)
                    st.info(insight_res)
                except Exception as e:
                    st.warning(f"Não foi possível gerar o relatório consolidado de insights agora. Erro: {e}")

else:
    st.warning("👈 Insira sua API Key da Groq na barra lateral para ativar a dashboard.")
