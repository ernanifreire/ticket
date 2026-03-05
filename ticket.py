import streamlit as st
import PyPDF2
import google.generativeai as genai
import pandas as pd
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets", layout="wide")

st.title("📊 Analisador Estratégico de Tickets")

with st.sidebar:
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # TENTATIVA 1: Nome padrão completo (costuma resolver o 404)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Teste de conexão silencioso
        try:
            model.generate_content("Oi", generation_config={"max_output_tokens": 1})
            st.sidebar.success("Conectado com Sucesso!")
        except Exception:
            # TENTATIVA 2: Se o Flash falhar, tentamos o Pro que é mais estável em algumas regiões
            model = genai.GenerativeModel('models/gemini-1.5-pro')
            st.sidebar.warning("Usando modelo Pro (Flash indisponível)")

    except Exception as e:
        st.error(f"Erro na configuração inicial: {e}")

    uploaded_files = st.file_uploader("Selecione seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                reader = PyPDF2.PdfReader(file)
                texto = ""
                for page in reader.pages:
                    texto += page.extract_text() or ""

                # Prompt otimizado para não gerar erros de caracteres
                prompt = f"""
                Analise este ticket e retorne os dados no formato CSV separado por ponto e vírgula (;).
                Campos: ID; Data; SLA; Problema; Causa_Raiz; Resolucao
                Ticket: {texto[:8000]}
                """

                # Chamada da IA
                response = model.generate_content(prompt)
                
                # Tratamento da resposta
                linha = response.text.replace('\n', ' ').strip().split(";")
                if len(linha) >= 5:
                    lista_dados.append(linha[:6])
                else:
                    lista_dados.append([file.name, "Erro de extração", "-", "-", "-", "-"])

            except Exception as e:
                st.error(f"Erro no arquivo {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if lista_dados:
            df = pd.DataFrame(lista_dados, columns=['ID', 'Data', 'SLA', 'Problema', 'Causa Raiz', 'Resolução'])
            st.subheader("📋 Resultado")
            st.dataframe(df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", output.getvalue(), "relatorio_tickets.xlsx")
else:
    st.warning("Aguardando API Key na barra lateral...")
