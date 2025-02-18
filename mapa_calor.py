import streamlit as st
import pandas as pd
import plotly.express as px
import pyodbc
import toml
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

# Configuração da página
st.set_page_config(
    page_title="Análise Compra e Venda",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. Temas e Estilização
# ==========================================
def init_theme():
    COLORS = ['#13428d', '#7C3AED', '#3B82F6', '#10B981', '#EF4444', '#F59E0B']
    COLORS_DARK = ['#1b4f72', '#d35400', '#145a32', '#7b241c', '#5b2c6f']

    ms = st.session_state
    if "themes" not in ms:
        ms.themes = {
            "current_theme": "light",
            "light": {
                "theme.base": "light",
                "theme.backgroundColor": "#FFFFFF",
                "theme.primaryColor": "#0095fb",
                "theme.secondaryBackgroundColor": "#F3F4F6",
                "theme.textColor": "#111827",
                "button_face": "Modo Escuro 🌙",
                "colors": COLORS,
            },
            "dark": {
                "theme.base": "dark",
                "theme.backgroundColor": "#1F2937",
                "theme.primaryColor": "#0095fb",
                "theme.secondaryBackgroundColor": "#4B5563",
                "theme.textColor": "#efefef",
                "button_face": "Modo Claro 🌞",
                "colors": COLORS_DARK,
            }
        }

def change_theme():
    ms = st.session_state
    current_theme = ms.themes["current_theme"]
    ms.themes["current_theme"] = "dark" if current_theme == "light" else "light"
    ms.themes["refreshed"] = True

def apply_custom_css():
    ms = st.session_state
    current_theme = ms.themes["current_theme"]
    theme_config = ms.themes[current_theme]
    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            background-color: {theme_config["theme.backgroundColor"]};
            color: {theme_config["theme.textColor"]};
        }}
        .stSelectbox > div > div {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
            color: {theme_config["theme.textColor"]} !important;
            border-radius: 5px;
            border: 2px solid {theme_config["theme.primaryColor"]} !important;
        }}
        .stSelectbox > div > div:hover {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: #FFFFFF !important;
            border: 2px solid {theme_config["theme.textColor"]} !important;
            border-radius: 5px;
            transition: border-color 0.3s ease-in-out;
        }}
        .stSelectbox > div > div::placeholder {{
            color: {theme_config["theme.textColor"]} !important;
            opacity: 0.7;
        }}
        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        .stDataFrame, .stMetric, .stJson, .stAlert,
        .stExpander .stMarkdown, .stTooltip, .stMetricValue {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        .stSidebar {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
            border-radius: 15px;
            padding: 10px;
        }}
        .nav-link.active {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .nav-link.active .icon {{
            color: #FFFFFF !important;
        }}
        .nav-link {{
            color: {theme_config["theme.textColor"]} !important;
            transition: background-color 0.3s, color 0.3s;
        }}
        .nav-link:hover {{
            background-color: {theme_config["theme.primaryColor"]}33;
            color: {theme_config["theme.primaryColor"]} !important;
        }}
        .stButton>button {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: #FFFFFF !important;
        }}
        .st-emotion-cache-1cj4yv0,
        .st-emotion-cache-efbu8t {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
        }}
        .stMultiSelect span[data-baseweb="tag"] {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: white !important;
        }}
        .stButton>button p {{
            color: white !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        [class*="stMetric"] {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        [class*="st-emotion-cache"] {{
            color: {theme_config["theme.primaryColor"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Inicializa tema e aplica CSS
init_theme()
apply_custom_css()

if st.button(st.session_state.themes[st.session_state.themes["current_theme"]]["button_face"], on_click=change_theme):
    pass

# ==========================================
# 2. Conexão com Banco de Dados e Consulta
# ==========================================
def get_db_credentials():
    return st.secrets["database"]

def get_connection():
    creds = get_db_credentials()
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={creds['server']};"
        f"DATABASE={creds['database']};"
        f"UID={creds['username']};"
        f"PWD={creds['password']}"
    )

def fetch_data():
    cnxn = get_connection()
    query = """
EXEC sp_HeatMapComprasVendas '2024-01-01', '2024-12-31'
    """
    try:
        cursor = cnxn.cursor()
        cursor.execute(query)
        if cursor.description is None:
            st.warning("A consulta não retornou dados.")
            return pd.DataFrame()
        rows = cursor.fetchall()
        # Se cada linha for um tuple com 1 elemento que é, por sua vez, uma tupla com os dados esperados, "desempacota"
        if rows and isinstance(rows[0][0], tuple):
            rows = [row[0] for row in rows]
        # Cria o DataFrame usando os nomes das colunas conforme o cursor.description
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        cnxn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

# ==========================================
# 3. Funções de Plotagem
# ==========================================
def plot_heatmap(data, column, title):
    try:
        pivot_table = data.pivot_table(index='COD_FABR', columns='MES', values=column, aggfunc='sum', fill_value=0)
        plt.figure(figsize=(14, 10))
        sns.heatmap(
            pivot_table,
            annot=True,
            fmt=".0f",
            cmap="coolwarm" if "Diferença" in title else "Blues",
            linewidths=0.5,
            cbar_kws={'label': 'Valor em R$'},
            norm=LogNorm() if column != 'DIFERENCA_VALORES' else None
        )
        plt.title(f'Heatmap de {title}', fontsize=14)
        plt.xlabel('Mês')
        plt.ylabel('Fabricante')
        st.pyplot(plt)
        plt.close()
    except Exception as e:
        st.error(f"Erro ao plotar heatmap de {title}: {e}")

def plot_bar_chart(data):
    st.subheader("Gráfico de Colunas")
    try:
        df_grouped = data.groupby('COD_FABR')[['VALOR_COMPRADO', 'VALOR_VENDIDO']].sum().reset_index()
        st.bar_chart(df_grouped.set_index('COD_FABR'))
    except Exception as e:
        st.error(f"Erro ao plotar gráfico de barras: {e}")

# ==========================================
# 4. Aplicação Principal
# ==========================================
st.title("Análise de Compras e Vendas por Fabricante")
df = fetch_data()

if df.empty:
    st.info("Nenhum dado foi retornado da consulta.")
else:
    # Seleciona o fabricante (caso as colunas estejam conforme o esperado)
    try:
        fabricantes = df['COD_FABR'].unique()
        escolha_fabricante = st.selectbox("Escolha o Fabricante", fabricantes)
        df_filtrado = df[df['COD_FABR'] == escolha_fabricante]
    
        plot_heatmap(df_filtrado, 'VALOR_COMPRADO', 'Compras')
        plot_heatmap(df_filtrado, 'VALOR_VENDIDO', 'Vendas')
        plot_heatmap(df_filtrado, 'DIFERENCA_VALORES', 'Diferença Compra-Venda')
        plot_bar_chart(df_filtrado)
    
        # Heatmap dos Top 10 Fabricantes
        mostrar_top10 = st.checkbox("Exibir Heatmap dos Top 10 Fabricantes Mais Comprados")
        if mostrar_top10:
            top10_fabricantes = df.groupby('COD_FABR')['VALOR_COMPRADO'].sum().nlargest(10).index
            df_top10 = df[df['COD_FABR'].isin(top10_fabricantes)]
            plot_heatmap(df_top10, 'VALOR_COMPRADO', 'Top 10 Fabricantes Mais Comprados')
    except KeyError as e:
        st.error(f"Erro ao acessar coluna no DataFrame: {e}")
