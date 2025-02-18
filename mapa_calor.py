import streamlit as st
import pandas as pd
import plotly.express as px
import pyodbc
import toml
import json  # necessário para converter JSON em dict, se for o caso
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

# Função para obter conexão com o banco de dados
def get_db_credentials():
    return st.secrets["database"]

# Use st.cache_resource para objetos não serializáveis, como conexões
@st.cache_resource
def get_connection():
    creds = get_db_credentials()
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={creds['server']};"
        f"DATABASE={creds['database']};"
        f"UID={creds['username']};"
        f"PWD={creds['password']}"
    )

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
# 2. Conexão com Banco de Dados e Consulta (MODIFICADO)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    try:
        with get_connection() as cnxn:
            # Ler diretamente com pandas
            df = pd.read_sql("""DECLARE @DataInicial DATE = '2024-01-01', 
        @DataFinal DATE = '2024-12-31';

-- CTE para Compras Corrigida
WITH ComprasCTE AS (
    SELECT
       f.CodFabr,
       f.NOMEFABR,
       YEAR(m.DtMov) AS Ano,
       MONTH(m.DtMov) AS Mes,
       SUM(dbo.fn_ValorItemMov2(im.IdItemMov, im.PrecoUnit, im.PercDescontoItem, m.PercDesconto, 'L') * im.Qtd) AS ValorComprado
    FROM Movimento m
    INNER JOIN ItensMov im ON m.IdMov = im.IdMov
    INNER JOIN Produtos p ON im.IdProduto = p.IdProduto
    INNER JOIN Fabricantes f ON p.CodFabr = f.CodFabr -- Corrigido o JOIN
    WHERE m.TipoMov IN ('1.1', '1.6')
      AND m.DtMov BETWEEN @DataInicial AND @DataFinal
    GROUP BY f.CodFabr, f.NOMEFABR, YEAR(m.DtMov), MONTH(m.DtMov)
),

-- CTE para Vendas (mantida igual)
Vendas AS (
    SELECT 
       bi.CodFabr,
       bi.nomefabr,
       bi.anovenda AS Ano,
       bi.mesvenda AS Mes,
       SUM(ISNULL(bi.vrvenda, 0)) AS ValorVendido
    FROM dbo.BI_CUBOVENDA bi WITH (NOLOCK)
    WHERE bi.codclifor LIKE 'C%'
      AND bi.codclifor NOT LIKE 'F%'
      AND bi.CondPag NOT IN (
          'MATERIAL PROMOCIONAL', 'AJUSTE INVENTARIO ENT, 30', 'SAIDA COMODATO', 'TROCA MERCANTIL', 'GARANTIA', 
          'DEVOLUÇÃO VENDA', 'TRANSF. FILIAL', 'DEMONSTRACAO', 'TROCA DE ELETRÔNICOS', 'TROCA', 'DEVOLUÇÃO DE COMODATO', 
          'DEVOLUÇÃO MERCANTIL', 'DEVOLUÇÃO DE CONCERTO', 'COMODATO VENDA', 'COBR DE INVENTÁRIO SKY', 'COBR DE SLOW MOVING SKY', 
          'DEVOLUÇÃO DE COMPRA', 'REMESSA P/ CONSERTO', 'ENTRADA COMODATO', 'BAIXA DE INCENDIO', 'BAIXA ESTOQUE/ PERCA', 
          'DESCONTO EM FOLHA', 'CREDITO DEV.VENDA', 'COMODATO EAF', 'COMODATO EAF SKY', 'COMODATO EAF VIVENSIS', 
          'COMODATO TELEVENDAS', 'USO INTERNO', 'DESCONTO EM FOLHA', 'FINANCEIRO - GERENCIAL', 'ATIVOS IMOBILIZADO'
      )
      AND bi.codclifor NOT IN (
          'C00001','C02687','C02694','C00914','C01909','C02142','C02175','C02398','C02448','C40004','C50132','C50133',
          'C50281','C50525','C50631','C50663','C50664','C50684','C50711','C50725','C50726','C50728','C50808','C50823',
          'C51074','C51144','C51229','C51237','C51238','C51312','C51387','C51411','C51427','C51539','C51544','C51585',
          'C51616','C51638','C51639','C51673','C51704','C51706','C51731','C51751','C51826','C51875','C51936','C51937',
          'C51957','C51969','C51988','C51994','C52001','C52030','C52042','C52046','C52052','C52106','C52119','C52121',
          'C52144','C52153','C52155','C52180','C52274','C52371','C52372','C52399','C52426','C52464','C52466','C52543',
          'C52649','C52710','C52713','C52720','C52836','C52926','C52988','C53007','C53008','C53036','C53074','C53075',
          'C53076','C53138','C53255','C53277','C53302','C53461','C53781'
      )
      AND bi.tipomovimento IN ('NF Venda', 'Pré-Venda')
      AND DATEFROMPARTS(bi.anovenda, bi.mesvenda, 1) BETWEEN @DataInicial AND @DataFinal
    GROUP BY bi.CodFabr, bi.nomefabr, bi.anovenda, bi.mesvenda
)

SELECT 
    COALESCE(c.CodFabr, v.CodFabr) AS COD_FABR,
    COALESCE(c.NOMEFABR, v.nomefabr) AS NOMEFABR,
    COALESCE(c.Ano, v.Ano) AS ANO,
    COALESCE(c.Mes, v.Mes) AS MES,
    ISNULL(c.ValorComprado, 0) AS VALOR_COMPRADO,
    ISNULL(v.ValorVendido, 0) AS VALOR_VENDIDO,
    ISNULL(c.ValorComprado, 0) - ISNULL(v.ValorVendido, 0) AS DIFERENCA_VALORES
FROM ComprasCTE c
FULL OUTER JOIN Vendas v
    ON c.CodFabr = v.CodFabr 
    AND c.Ano = v.Ano 
    AND c.Mes = v.Mes
ORDER BY NOMEFABR, ANO, MES;""", cnxn)
            # Se a coluna dos meses vem sem acento, renomeia para 'Mês'
            if 'Mes' in df.columns and 'Mês' not in df.columns:
                df = df.rename(columns={'Mes': 'Mês'})
            return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

# ==========================================
# Função auxiliar para formatação de moeda no padrão brasileiro
# ==========================================
def format_currency(value):
    formatted = f"R$ {value:,.2f}"
    formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return formatted

# ==========================================
# 3. Funções de Plotagem (ATUALIZADO)
# ==========================================
def plot_heatmap(data, column, title):
    try:
        if column not in data.columns:
            st.error(f"Coluna '{column}' não encontrada nos dados")
            return
        # Cria uma cópia para formatação do mês, sem alterar o DataFrame original
        plot_data = data.copy()
        if 'Mês' in plot_data.columns:
            plot_data['Mês'] = pd.Categorical(
                plot_data['Mês'],
                categories=['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                ordered=True
            )
        pivot_table = plot_data.pivot_table(
            index='NOMEFABR', 
            columns='Mês', 
            values=column, 
            aggfunc='sum', 
            fill_value=0
        )
        fig = px.imshow(
            pivot_table,
            labels=dict(x="Mês", y="Fabricante", color="Valor (R$)"),
            title=f'Heatmap de {title}',
            color_continuous_scale='Blues' if 'Compra' in title else 'Reds',
            text_auto=".2s"
        )
        fig.update_layout(
            xaxis=dict(side="top", tickangle=-45),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao plotar heatmap: {str(e)}")

def plot_bar_chart(data):
    st.subheader("Gráfico de Colunas")
    try:
        df_grouped = data.groupby('NOMEFABR')[['VALOR_COMPRADO', 'VALOR_VENDIDO']].sum().reset_index()
        st.bar_chart(df_grouped.set_index('NOMEFABR'))
    except Exception as e:
        st.error(f"Erro ao plotar gráfico de barras: {e}")

# ==========================================
# 4. Aplicação Principal (ATUALIZADO)
# ==========================================
st.title("Análise de Compras e Vendas por Fabricante")
df = fetch_data()

if df.empty:
    st.info("Nenhum dado foi retornado da consulta.")
else:
    try:
        # Renomeia colunas para padronização
        df = df.rename(columns={
            'ValorComprado': 'VALOR_COMPRADO',
            'ValorVendido': 'VALOR_VENDIDO',
            'DiferencaValores': 'DIFERENCA_VALORES'
        })
        
        # Lista de fabricantes com opção 'Todos'
        fabricantes = ['Todos'] + sorted(df['NOMEFABR'].unique().tolist())
        escolha_fabricante = st.selectbox("Escolha o Fabricante", fabricantes, index=0)
        
        if escolha_fabricante != 'Todos':
            df = df[df['NOMEFABR'] == escolha_fabricante]
        
        # Exibe métricas com formatação brasileira
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Comprado", format_currency(df['VALOR_COMPRADO'].sum()))
        col2.metric("Total Vendido", format_currency(df['VALOR_VENDIDO'].sum()))
        col3.metric("Diferença", format_currency(df['DIFERENCA_VALORES'].sum()))
        
        # Exibe os dados tabelados em um expander
        with st.expander("Ver dados completos"):
            st.dataframe(df)
        
        # Abas para visualizações
        tab1, tab2, tab3 = st.tabs(["Compras", "Vendas", "Diferença"])
        with tab1:
            plot_heatmap(df, 'VALOR_COMPRADO', 'Compras')
        with tab2:
            plot_heatmap(df, 'VALOR_VENDIDO', 'Vendas')
        with tab3:
            plot_heatmap(df, 'DIFERENCA_VALORES', 'Diferença Compra-Venda')
        
        # Gráfico de barras
        plot_bar_chart(df)
        
        # Top 10 Fabricantes (apenas se 'Todos' estiver selecionado)
        if escolha_fabricante == 'Todos':
            st.subheader("Top 10 Fabricantes")
            top10 = df.groupby('NOMEFABR').agg({
                'VALOR_COMPRADO': 'sum',
                'VALOR_VENDIDO': 'sum',
                'DIFERENCA_VALORES': 'sum'
            }).nlargest(10, 'VALOR_VENDIDO')
            st.dataframe(
                top10.style.format({
                    'VALOR_COMPRADO': lambda x: format_currency(x),
                    'VALOR_VENDIDO': lambda x: format_currency(x),
                    'DIFERENCA_VALORES': lambda x: format_currency(x)
                }),
                use_container_width=True
            )
            
    except KeyError as e:
        st.error(f"Erro de estrutura de dados: {str(e)}")
        st.write("Colunas disponíveis:", df.columns.tolist())
