import streamlit as st
import PyPDF2
from groq import Groq
import pandas as pd
import io
import plotly.express as px
import time

# ... (Configurações iniciais de página e barra lateral iguais) ...

def chamar_ia(api_key, system_prompt, user_content):
    client = Groq(api_key=api_key)
    # Mudamos para o modelo 8b-instant: limite de tokens muito maior e mais estável
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        model="llama-3.1-8b-instant", 
        temperature=0.1,
    )
    return chat_completion.choices[0].message.content.strip()

# ... (Dentro do loop de processamento de arquivos) ...

            # LIMITADOR DE TEXTO: Pegamos os primeiros 4k e os últimos 4k caracteres 
            # (Onde geralmente estão a abertura e o desfecho/resolução do ticket)
            texto_reduzido = texto_completo[:4000] + "\n[...]\n" + texto_completo[-4000:]

            try:
                # Chamada com o texto otimizado para economizar tokens
                resultado_ia = chamar_ia(api_key, system_prompt, f"Analise: {texto_reduzido}")
                # ... (resto do tratamento de colunas) ...
            except Exception as e:
                if "rate_limit_exceeded" in str(e).lower():
                    st.error(f"Limite atingido no arquivo {file.name}. Aguardando 10 segundos...")
                    time.sleep(10) # Pausa estratégica para limpar o limite
                    continue
