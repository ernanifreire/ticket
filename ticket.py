import streamlit as st
import PyPDF2
from groq import Groq
import pandas as pd
import io
import plotly.express as px
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Suporte Estratégico", layout="wide")

st.title("📊 Dashboard de Análise de Tickets e Causa Raiz")
st.markdown("Análise profunda de históricos de chat para redução de volume e melhoria de TMA.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("Insira sua Groq API Key:", type="password")
    st.info("Obtenha grátis em: console.groq.com")
    st.divider()
    st.markdown("### Plano de Ataque:")
    st.write("Esta ferramenta identifica gargalos operacionais e falhas de produto através da análise de causa raiz.")

# --- FUNÇÃO DE CHAMADA À IA ---
def chamar_ia(api_key, system_prompt, user_content):
    client = Groq(api_key=api_key)
    # Modelo 8b-instant é 10x mais rápido e tem limites de cota maiores
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.1,
    )
    return chat_completion.choices[0].message.content.strip()

# --- LÓGICA PRINCIPAL ---
if api_key:
    uploaded_files = st.file_uploader("Selecione até 20 PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise Profunda"):
        lista_dados = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, file in enumerate(uploaded_files[:20]):
            status_text.text(f"Analisando: {file.name}")
            
            try:
                # 1. Extração do PDF
                reader = PyPDF2.PdfReader(file)
                texto_completo = "".join([page.extract_text() or "" for page in reader.pages])

                # 2. Truncagem Estratégica para economizar tokens e evitar Erro 429
                # Pegamos o início (contexto) e o fim (desfecho) do chat
                texto_reduzido = texto_completo[:4000] + "\n[...]\n" + texto_completo[-4000:]

                # 3. Prompt de Extração
                system_p = """
                Analise logs de suporte. Retorne APENAS uma linha CSV com ponto e vírgula (;).
                Campos: ID;Data_Inicio;TMA_Minutos;Problema;Causa_Raiz;Categoria;Resolucao;Qualidade_1_a_5
                """
                
                # 4. Chamada da IA
                resultado = chamar_ia(api_key, system_p, f"Ticket: {texto_reduzido}")
                
                # 5. Tratamento de dados
                dados = resultado.replace('\n', ' ').strip().split(";")
                if len(dados) >= 7:
                    lista_dados.append(dados[:8])
                
                # Pausa curta para não sobrecarregar a API
                time.sleep(0.5)

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files[:20]))

        status_text.text("Processamento concluído!")

        # --- DASHBOARD E GRÁFICOS ---
        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=[
                'ID', 'Data', 'TMA', 'Problema', 'Causa Raiz', 'Categoria', 'Resolução', 'Score'
            ])
            
            # Limpeza de números
            df['TMA'] = pd.to_numeric(df['TMA'], errors='coerce').fillna(0)
            df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(0)

            st.divider()
            
            # KPIs rápidos
            col1, col2, col3 = st.columns(3)
            col1.metric("Tickets Analisados", len(df))
            col2.metric("Tempo Médio (TMA)", f"{df['TMA'].mean():.1f} min")
            col3.metric("Satisfação Média", f"{df['Score'].mean():.1f} ⭐")

            # Gráfico de Barras: Categorias
            st.subheader("📌 Volume por Categoria")
            fig_cat = px.bar(df['Categoria'].value_counts().reset_index(), x='count', y='Categoria', orientation='h', title="Gargalos por Categoria")
            st.plotly_chart(fig_cat, use_container_width=True)
            
            

            # Tabela Final
            st.subheader("📋 Dados Consolidados")
            st.dataframe(df, use_container_width=True)

            # Download Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Relatório Completo", output.getvalue(), "analise_suporte.xlsx")

            # --- INSIGHTS DE ATAQUE ---
            st.divider()
            st.subheader("💡 Plano de Ataque Sugerido")
            causas = " | ".join(df['Causa Raiz'].unique())
            insights = chamar_ia(api_key, "Você é um gestor de CX.", f"Com base nessas causas raízes, cite 3 ações para reduzir o volume de tickets em 20%: {causas}")
            st.info(insights)

else:
    st.warning("Insira sua Groq API Key para começar.")
