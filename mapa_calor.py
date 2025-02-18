import streamlit as st
import pandas as pd
import plotly.express as px
import pyodbc
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Análise Compra e Venda",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. Temas e Estilização (Otimizado)
# ==========================================
def init_theme():
    if "themes" not in st.session_state:
        st.session_state.themes = {
            "current_theme": "light",
            "light": {
                "theme.base": "light",
                "button_face": "🌙 Modo Escuro",
                "colors": px.colors.qualitative.Plotly
            },
            "dark": {
                "theme.base": "dark",
                "button_face": "🌞 Modo Claro",
                "colors": px.colors.qualitative.Dark24
            }
        }

def apply_theme():
    theme = st.session_state.themes[st.session_state.themes["current_theme"]]
    config = {
        "layout": {"plot_bgcolor": "rgba(0,0,0,0)"},
        "font": {"color": "#2c3e50" if theme["theme.base"] == "light" else "#f5f6fa"}
    }
    px.defaults.template = "plotly_white" if theme["theme.base"] == "light" else "plotly_dark"
    px.defaults.color_continuous_scale = theme["colors"]
    return config

init_theme()

# ==========================================
# 2. Conexão com Banco de Dados (Com cache)
# ==========================================
@st.cache_data(ttl=3600)
def get_connection():
    creds = st.secrets["database"]
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={creds['server']};"
        f"DATABASE={creds['database']};"
        f"UID={creds['username']};"
        f"PWD={creds['password']}"
    )

@st.cache_data(ttl=300)
def fetch_data(start_date, end_date):
    try:
        with get_connection() as cnxn:
            df = pd.read_sql(
                f"EXEC sp_HeatMapComprasVendas '{start_date}', '{end_date}'", 
                cnxn
            )
            
            # Converter meses para formato categórico ordenado
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            df['MES'] = pd.Categorical(df['MES'], categories=meses, ordered=True)
            
            return df
    except Exception as e:
        st.error(f"Erro na conexão com o banco: {e}")
        return pd.DataFrame()

# ==========================================
# 3. Funções de Visualização (Plotly)
# ==========================================
def plot_heatmap(data, column, title):
    try:
        pivot = data.pivot_table(
            index='NOME_FABR',
            columns='MES',
            values=column,
            aggfunc='sum',
            fill_value=0
        )
        
        # Ordenar por soma total
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
        
        fig = px.imshow(
            pivot,
            labels=dict(x="Mês", y="Fabricante", color=title.split()[-1]),
            title=title,
            color_continuous_scale='Blues' if 'Compra' in title else 'Reds' if 'Venda' in title else 'RdBu_r',
            text_auto=".2s"  # Formatação automática
        )
        
        fig.update_layout(
            xaxis=dict(side="top", tickangle=-45),
            height=800,
            coloraxis_colorbar=dict(title="R$")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao gerar heatmap: {str(e)}")

def plot_metricas(data):
    cols = st.columns(3)
    metricas = {
        "Total Comprado": data['VALOR_COMPRADO'].sum(),
        "Total Vendido": data['VALOR_VENDIDO'].sum(),
        "Balanço": data['DIFERENCA_VALORES'].sum()
    }
    
    for (k, v), col in zip(metricas.items(), cols):
        col.metric(
            label=k,
            value=f"R$ {v:,.2f}",
            delta=f"R$ {data['DIFERENCA_VALORES'].sum():,.2f}" if k == "Balanço" else None
        )

# ==========================================
# 4. Aplicação Principal
# ==========================================
def main():
    # Controles de Data
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Inicial", datetime(2024, 1, 1))
    with col2:
        end_date = st.date_input("Data Final", datetime(2024, 12, 31))
    
    # Carregar dados
    df = fetch_data(start_date, end_date)
    
    if df.empty:
        st.warning("Nenhum dado encontrado para o período selecionado")
        return
    
    # Sidebar - Controles
    with st.sidebar:
        st.title("Filtros")
        fabricante = st.selectbox(
            "Selecione o Fabricante",
            options=['Todos'] + sorted(df['NOME_FABR'].unique().tolist())
        )
        
        if st.button(st.session_state.themes[st.session_state.themes["current_theme"]]["button_face"]):
            change_theme()
    
    # Aplicar tema
    theme_config = apply_theme()
    
    # Filtrar dados
    if fabricante != 'Todos':
        df = df[df['NOME_FABR'] == fabricante]
    
    # Visualizações
    st.title("Análise de Compras e Vendas")
    plot_metricas(df)
    
    tab1, tab2, tab3 = st.tabs(["Compras", "Vendas", "Balanço"])
    
    with tab1:
        plot_heatmap(df, 'VALOR_COMPRADO', 'Heatmap de Compras')
    
    with tab2:
        plot_heatmap(df, 'VALOR_VENDIDO', 'Heatmap de Vendas')
    
    with tab3:
        plot_heatmap(df, 'DIFERENCA_VALORES', 'Balanço Compra vs Venda')
    
    # Análise Top 10
    if fabricante == 'Todos':
        st.header("Top 10 Fabricantes")
        top10 = df.groupby('NOME_FABR')[['VALOR_COMPRADO', 'VALOR_VENDIDO']].sum()
        top10['Balanço'] = top10['VALOR_VENDIDO'] - top10['VALOR_COMPRADO']
        st.dataframe(
            top10.nlargest(10, 'VALOR_COMPRADO').style.format("{:,.2f}"),
            use_container_width=True
        )

def change_theme():
    current = st.session_state.themes["current_theme"]
    st.session_state.themes["current_theme"] = "dark" if current == "light" else "light"

if __name__ == "__main__":
    main()