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

st.set_page_config(
    page_title="Análise Compra e Venda",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded")

def page_compra_venda():
     # Paleta de cores atualizada
    COLORS = ['#13428d', '#7C3AED', '#3B82F6', '#10B981', '#EF4444', '#F59E0B']
    COLORS_DARK = ['#1b4f72', '#d35400', '#145a32', '#7b241c', '#5b2c6f']

    # Configuração do tema no session_state
    ms = st.session_state
    if "themes" not in ms:
        ms.themes = {
            "current_theme": "light",
            "light": {
                "theme.base": "light",
                "theme.backgroundColor": "#FFFFFF",  # Cor de fundo
                "theme.primaryColor": "#0095fb",     # Cor primária (botões, links)
                "theme.secondaryBackgroundColor": "#F3F4F6",  # Cor de fundo secundária
                "theme.textColor": "#111827",        # Cor do texto
                "button_face": "Modo Escuro 🌙",     # Texto do botão
                "colors": COLORS,                    # Paleta de cores
            },
            "dark": {
                "theme.base": "dark",
                "theme.backgroundColor": "#1F2937",  # Cor de fundo
                "theme.primaryColor": "#0095fb",     # Cor primária (botões, links)
                "theme.secondaryBackgroundColor": "#4B5563",  # Cor de fundo secundária
                "theme.textColor": "#efefef",        # Cor do texto
                "button_face": "Modo Claro 🌞",      # Texto do botão
                "colors": COLORS_DARK,               # Paleta de cores
            }
        }

    # Função para alternar o tema
    def change_theme():
        current_theme = ms.themes["current_theme"]
        ms.themes["current_theme"] = "dark" if current_theme == "light" else "light"
        ms.themes["refreshed"] = True  # Atualiza o estado

    # Configuração do tema atual
    current_theme = ms.themes["current_theme"]
    theme_config = ms.themes[current_theme]

     # Botão de alternar tema
    if st.button(theme_config["button_face"], on_click=change_theme):
        pass


    # Aplicar as cores do tema atual
    colors = theme_config["colors"]

    # Injetar CSS personalizado com base no tema atual
    st.markdown(
        f"""
        <style>
        /* ===== [CONFIGURAÇÃO GLOBAL] ===== */
        html, body, .stApp {{
            background-color: {theme_config["theme.backgroundColor"]};
            color: {theme_config["theme.textColor"]};
        }}

        /* ===== [COMPONENTES DO STREAMLIT] ===== */
        /* Ajuste para Selectbox */
        .stSelectbox > div > div {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
            color: {theme_config["theme.textColor"]} !important;
            border-radius: 5px; /* Bordas arredondadas */
            border: 2px solid {theme_config["theme.primaryColor"]} !important; /* Cor oposta do tema */
        }}

        .stSelectbox > div > div:hover {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: #FFFFFF !important;
              border: 2px solid {theme_config["theme.textColor"]} !important; /* Cor oposta do tema */
        border-radius: 5px; /* Bordas arredondadas */
        transition: border-color 0.3s ease-in-out; /* Suaviza a transição */

        }}

        /* Placeholder ajustado */
        .stSelectbox > div > div::placeholder {{
            color: {theme_config["theme.textColor"]} !important;
            opacity: 0.7;
        }}

        
        /* ===== [CABEÇALHOS E TÍTULOS] ===== */
        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
            color: {theme_config["theme.textColor"]} !important;
        }}

    /* ===== [COMPONENTES PRINCIPAIS] ===== */
        .stDataFrame, .stMetric, .stJson, .stAlert,
        .stExpander .stMarkdown, .stTooltip, .stMetricValue {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        
        
        /* ===== [SIDEBAR] ===== */
        .stSidebar {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
            border-radius: 15px;
            padding: 10px;
        }}
         .nav-link.active {{
        background-color: {theme_config["theme.primaryColor"]} !important;
        color: #FFFFFF !important; /* Texto branco para contraste */
        font-weight: bold !important; /* Texto em negrito para destaque */
        border-radius: 8px; /* Bordas arredondadas */
        padding: 10px; /* Espaçamento interno */
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); /* Sombra para destaque */
    }}

    /* Ícones dentro do item ativo */
    .nav-link.active .icon {{
        color: #FFFFFF !important; /* Altera a cor do ícone no item ativo */
    }}

    /* Estilo para itens inativos */
    .nav-link {{
        color: {theme_config["theme.textColor"]} !important; /* Cor do texto do tema */
        transition: background-color 0.3s, color 0.3s; /* Transição suave ao passar o mouse */
    }}

    .nav-link:hover {{
        background-color: {theme_config["theme.primaryColor"]}33; /* Cor primária translúcida */
        color: {theme_config["theme.primaryColor"]} !important; /* Texto na cor primária */
    }}

        /* Ajusta texto e fundo nos botões */
        .stButton>button {{
            background-color: {theme_config["theme.primaryColor"]} !important;
            color: #FFFFFF !important;
        }}

        /* ===== [GENÉRICO] ===== */
        /* Ajusta elementos dinâmicos */
        .st-emotion-cache-1cj4yv0,
        .st-emotion-cache-efbu8t {{
            background-color: {theme_config["theme.secondaryBackgroundColor"]} !important;
        
        }}
        
        /* ===== [COMPONENTES ESPECÍFICOS] ===== */
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

        [class*="stMetric"]
        {{
            color: {theme_config["theme.textColor"]} !important;
        }}
        
        [class*="st-emotion-cache"] {{
            color: {theme_config["theme.primaryColor"]} !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# Carregar credenciais do secrets.toml
def get_db_credentials():
    return st.secrets["database"]

# Conectar ao banco de dados
def get_connection():
    creds = get_db_credentials()
    return pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={creds['server']};DATABASE={creds['database']};UID={creds['username']};PWD={creds['password']}")

# Consulta os dados do banco de dados
def fetch_data():
    cnxn = get_connection()
    query = """
 DECLARE @DataInicial DATE = '2024-01-01', 
        @DataFinal DATE = '2024-12-31';

WITH HeatMap AS (
    SELECT 
        F.CodFabr,
        F.NomeFabr,
        YEAR(m.DtMov) AS Ano,
        MONTH(m.DtMov) AS Mes,
        SUM(im.Qtd * dbo.fn_ValorItemMov2(im.IdItemMov, im.PrecoUnit, im.PercDescontoItem, m.PercDesconto, 'L')) AS ValorComprado,
        0 AS ValorVendido
    FROM Movimento m
    INNER JOIN ItensMov im ON m.IdMov = im.IdMov
    INNER JOIN Produtos p ON im.IdProduto = p.IdProduto
    INNER JOIN Fabricantes f ON p.CodFabr = f.IdEmpresa
    WHERE m.TipoMov IN ('1.1', '1.6')
        AND m.DtMov BETWEEN @DataInicial AND @DataFinal
    GROUP BY f.CodFabr, f.NomeFabr, YEAR(m.DtMov), MONTH(m.DtMov)

    UNION ALL

    SELECT 
        bi.CodFabr,
        f.NomeFabr,
        bi.anovenda AS Ano,
        bi.mesvenda AS Mes,
        0 AS ValorComprado,
        SUM(ISNULL(bi.vrvenda, 0)) AS ValorVendido
    FROM dbo.BI_CUBOVENDA bi
    INNER JOIN Fabricantes f ON bi.CodFabr = f.CodFabr
    WHERE bi.codclifor LIKE 'C%'
        AND bi.codclifor NOT LIKE 'F%'
        AND bi.CondPag NOT IN ('MATERIAL PROMOCIONAL', 'AJUSTE INVENTARIO ENT, 30', 'SAIDA COMODATO', 'TROCA MERCANTIL', 'GARANTIA', 'DEVOLUÇÃO VENDA', 'TRANSF. FILIAL', 'DEMONSTRACAO', 'TROCA DE ELETRÔNICOS', 'TROCA', 'DEVOLUÇÃO DE COMODATO', 'DEVOLUÇÃO MERCANTIL', 'DEVOLUÇÃO DE CONCERTO', 'COMODATO VENDA', 'COBR DE INVENTÁRIO SKY', 'COBR DE SLOW MOVING SKY', 'DEVOLUÇÃO DE COMPRA', 'REMESSA P/ CONSERTO', 'ENTRADA COMODATO', 'BAIXA DE INCENDIO', 'BAIXA ESTOQUE/ PERCA', 'DESCONTO EM FOLHA', 'CREDITO DEV.VENDA', 'COMODATO EAF', 'COMODATO EAF SKY', 'COMODATO EAF VIVENSIS', 'COMODATO TELEVENDAS', 'USO INTERNO', 'DESCONTO EM FOLHA', 'FINANCEIRO - GERENCIAL', 'ATIVOS IMOBILIZADO')
        AND bi.codclifor NOT IN ('C00001','C02687','C02694','C00914','C01909','C02142','C02175','C02398','C02448','C40004','C50132','C50133','C50281','C50525','C50631','C50663','C50664','C50684','C50711','C50725','C50726','C50728','C50808','C50823','C51074','C51144','C51229','C51237','C51238','C51312','C51387','C51411','C51427','C51539','C51544','C51585','C51616','C51638','C51639','C51673','C51704','C51706','C51731','C51751','C51826','C51875','C51936','C51937','C51957','C51969','C51988','C51994','C52001','C52030','C52042','C52046','C52052','C52106','C52119','C52121','C52144','C52153','C52155','C52180','C52274','C52371','C52372','C52399','C52426','C52464','C52466','C52543','C52649','C52710','C52713','C52720','C52836','C52926','C52988','C53007','C53008','C53036','C53074','C53075','C53076','C53138','C53255','C53277','C53302','C53461','C53781')
        AND bi.tipomovimento IN ('NF Venda', 'Pré-Venda')
        AND DATEFROMPARTS(bi.anovenda, bi.mesvenda, 1) BETWEEN @DataInicial AND @DataFinal
    GROUP BY bi.CodFabr, f.NomeFabr, bi.anovenda, bi.mesvenda
)

SELECT 
    CodFabr AS COD_FABR,
    NomeFabr AS NOME_FABR,
    Ano AS ANO,
    Mes AS MES,
    SUM(ValorComprado) AS VALOR_COMPRADO,
    SUM(ValorVendido) AS VALOR_VENDIDO,
    SUM(ValorComprado) - SUM(ValorVendido) AS DIFERENCA_VALORES
FROM HeatMap
GROUP BY CodFabr, NomeFabr, Ano, Mes;



    """
    
    try:
        cursor = cnxn.cursor()
        cursor.execute(query)
        if cursor.description is None:
            st.warning("A consulta não retornou dados.")
            return pd.DataFrame()  # Retorna um DataFrame vazio para evitar erro
        
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        cnxn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

# Criar Heatmap
def plot_heatmap(data, column, title):
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

# Criar gráfico de colunas
def plot_bar_chart(data):
    st.subheader("Gráfico de Colunas")
    df_grouped = data.groupby('COD_FABR')[['VALOR_COMPRADO', 'VALOR_VENDIDO']].sum().reset_index()
    st.bar_chart(df_grouped.set_index('COD_FABR'))

# Aplicação Streamlit
st.title("Análise de Compras e Vendas por Fabricante")
df = fetch_data()

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
