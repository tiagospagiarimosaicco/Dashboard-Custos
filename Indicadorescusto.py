# VERSÃO DEFINITIVA STREAMLIT - CÁLCULOS VALIDADOS E VISUAL CORPORATIVO
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================

st.set_page_config(layout="wide", page_title="Dashboard de Custos | Mosaic")

# CSS para criar o layout de "cards", ajustar fontes e aplicar o tema Mosaic
st.markdown("""
<style>
    /* Fundo geral da página */
    .main > div {
        background-color: #F5F7FA;
        padding: 2rem 2rem 10rem 2rem;
    }
    /* Estilo do Card genérico */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 25px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
    }
    /* Estilos dos Títulos Principais */
    .main-header {
        font-size: 2.8rem !important;
        font-weight: bold !important;
        color: #002776 !important;
        padding-bottom: 10px;
    }
    .sub-header {
        font-size: 1.3rem !important;
        color: #4D4D4F !important;
        padding-bottom: 20px;
    }
    /* Ajustes nos KPIs Nativos do Streamlit para o tema */
    .st-emotion-cache-1g6goon h4 { /* Título do KPI */
        font-size: 16px !important;
        font-weight: bold !important;
        color: #555 !important;
    }
    .st-emotion-cache-1g6goon p { /* Valor do KPI */
        font-size: 28px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARREGAMENTO DE DADOS E FUNÇÕES
# ==============================================================================

@st.cache_data
def carregar_dados(caminho_arquivo):
    """Carrega, limpa e prepara os dados para o dashboard."""
    # Usei o método de ler a partir de um texto para testar com seus dados do mês 8
    # Mantenha a leitura do seu arquivo excel/github para a versão completa
    df = pd.read_excel(caminho_arquivo)

    # Lógica de limpeza (revisada e validada)
    df['Planta'] = df['Planta'].ffill()
    df['Data de lançamento'] = pd.to_datetime(df['Data de lançamento'], dayfirst=True, errors='coerce')
    def clean_currency(value):
        try: return float(str(value).replace('.', '').replace(',', '.'))
        except (ValueError, TypeError): return 0.0
    df['Valor/MR'] = df['Valor/MR'].apply(clean_currency)
    df['Centro custo'] = df['Centro custo'].astype(str).str.strip()
    df['Tipo de documento'] = df['Tipo de documento'].astype(str).str.strip()
    df.dropna(subset=['Data de lançamento', 'Valor/MR', 'Centro custo'], inplace=True)
    df['Ano-Mês'] = df['Data de lançamento'].dt.strftime('%Y-%m')
    df.rename(columns={'Denom.classe custo': 'Classe de Custo'}, inplace=True)
    return df

# Para usar seu arquivo completo, volte a usar uma das linhas abaixo:
# df = carregar_dados("Execução CCs Almoxarifados 2025 - 21.08.25.xlsx")
# df = carregar_dados_privados() # Se estiver usando a versão com GitHub
df = carregar_dados("Execução CCs Almoxarifados 2025 - 21.08.25.xlsx")


# Paleta de Cores Mosaic
MOSAIC_COLORS = {"azul_escuro": "#002776", "azul_claro": "#00AEEF", "verde": "#78BE20", "teal": "#007C91"}

# ==============================================================================
# 3. BARRA LATERAL COM FILTROS ESTRATÉGICOS
# ==============================================================================
st.sidebar.image("assets/logo.png", width=200)
st.sidebar.title("Painel de Controle")
st.sidebar.markdown("---")

# Filtros
ccs_options = ['(Todos)'] + sorted(df['Centro custo'].unique())
cc_selecionado = st.sidebar.selectbox("Filtrar por Centro de Custo:", options=ccs_options)

data_min = df['Data de lançamento'].min().date()
data_max = df['Data de lançamento'].max().date()
data_inicio = st.sidebar.date_input("Data Inicial:", value=data_min, min_value=data_min, max_value=data_max)
data_fim = st.sidebar.date_input("Data Final:", value=data_max, min_value=data_inicio, max_value=data_max)

# Lógica de filtro reativa e funcional
df_filtrado = df.copy()
if cc_selecionado != '(Todos)':
    df_filtrado = df_filtrado[df_filtrado['Centro custo'] == cc_selecionado]
df_filtrado = df_filtrado[(df_filtrado['Data de lançamento'].dt.date >= data_inicio) & (df_filtrado['Data de lançamento'].dt.date <= data_fim)]

# ==============================================================================
# 4. LAYOUT PRINCIPAL DO DASHBOARD
# ==============================================================================

st.markdown('<p class="main-header">Dashboard Corporativo de Custos</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Análise de Custos Realizados nos Centros de Custo de Almoxarifado</p>', unsafe_allow_html=True)

# --- KPIs em Cards com Entradas e Saídas ---
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if not df_filtrado.empty:
        saidas = df_filtrado[df_filtrado['Valor/MR'] < 0]['Valor/MR'].sum()
        entradas = df_filtrado[df_filtrado['Valor/MR'] > 0]['Valor/MR'].sum()
        saldo_liquido = df_filtrado['Valor/MR'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Débitos (Saídas)", f"R$ {saidas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("Total de Créditos (Entradas)", f"R$ {entradas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("SALDO LÍQUIDO", f"R$ {saldo_liquido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="inverse")
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Gráficos em Cards ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    custo_mensal = df_filtrado.groupby('Ano-Mês')['Valor/MR'].sum().reset_index()
    fig_linha = px.line(custo_mensal, x='Ano-Mês', y='Valor/MR', title="Evolução do Saldo Líquido Mensal", markers=True, color_discrete_sequence=[MOSAIC_COLORS['azul_claro']])
    fig_linha.update_layout(plot_bgcolor='white', title_font_size=20, height=450)
    st.plotly_chart(fig_linha, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_graf2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    custo_por_classe = df_filtrado.groupby('Classe de Custo')['Valor/MR'].sum().nlargest(10).sort_values()
    fig_barras = px.bar(custo_por_classe, x='Valor/MR', y=custo_por_classe.index, orientation='h', text=custo_por_classe.values, color_discrete_sequence=[MOSAIC_COLORS['teal']])
    fig_barras.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
    fig_barras.update_layout(title_text="Top 10 Classes de Custo (Saldo Líquido)", plot_bgcolor='white', yaxis={'categoryorder':'total ascending'}, title_font_size=20, height=450)
    st.plotly_chart(fig_barras, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tabela Detalhada em um Card ---
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Detalhamento dos Lançamentos")
    colunas_uteis = ['Data de lançamento', 'Centro custo', 'Classe de Custo', 'Descrição material', 'Tipo de documento', 'Nome do usuário', 'Nº doc.de referência', 'Valor/MR']
    colunas_existentes = [col for col in colunas_uteis if col in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_existentes].style.format({"Valor/MR": "R$ {:,.2f}", "Data de lançamento": "{:%d/%m/%Y}"}))
    st.markdown('</div>', unsafe_allow_html=True)
