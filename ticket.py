import streamlit as st
import PyPDF2
import pandas as pd
import io
import requests
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador de Tickets", layout="wide")
st.title("📊 Analisador Estratégico de Tickets (Conexão Direta v1)")

with st.sidebar:
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")

# --- FUNÇÃO DE CHAMADA DIRETA À API (SEM BIBLIOTECA BUGADA) ---
def chamar_gemini_direto(api_key, prompt_text):
    # Forçamos a URL da versão estável V1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"Erro na API ({response.status_code}): {response.text}")

# --- LÓGICA DO APP ---
if api_key:
    uploaded_files = st.file_uploader("Suba seus PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar Análise"):
        lista_dados = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                # 1. Extração do PDF
                reader = PyPDF2.PdfReader(file)
                texto_completo = ""
                for page in reader.pages:
                    texto_completo += page.extract_text() or ""

                # 2. Prompt de Extração
                prompt = f"""
                Analise este ticket e retorne APENAS uma linha CSV separada por ponto e vírgula (;).
                Campos: ID; Data; SLA; Problema; Causa_Raiz; Resolucao
                Ticket: {texto_ticket[:8000] if 'texto_ticket' in locals() else texto_completo[:8000]}
                """

                # 3. Chamada Direta
                resultado_ia = chamar_gemini_direto(api_key, prompt)
                
                # 4. Tratamento dos dados
                linha = resultado_ia.replace('\n', ' ').strip().split(";")
                if len(linha) >= 5:
                    lista_dados.append(linha[:6])
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
    st.warning("Insira a API Key na barra lateral.")
