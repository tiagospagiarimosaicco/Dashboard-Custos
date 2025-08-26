# VERSÃO DEFINITIVA - LEITURA SEGURA DE DADOS DE REPOSITÓRIO PRIVADO
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(layout="wide", page_title="Dashboard de Custos | Mosaic")
# ... (O CSS do layout de cards continua o mesmo da versão anterior) ...
st.markdown("""
<style>
    .main > div {background-color: #F5F7FA; padding: 2rem 2rem 10rem 2rem;}
    .card {background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; height: 100%;}
    .main-header {font-size: 2.8rem !important; font-weight: bold !important; color: #002776 !important; padding-bottom: 10px;}
    .sub-header {font-size: 1.3rem !important; color: #4D4D4F !important; padding-bottom: 20px;}
    .st-emotion-cache-1g6goon h4 {font-size: 16px !important; font-weight: bold !important; color: #555 !important;}
    .st-emotion-cache-1g6goon p {font-size: 28px !important; font-weight: bold !important; color: #002776 !important;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARREGAMENTO SEGURO DE DADOS
# ==============================================================================
@st.cache_data(ttl=600) # Cache de 10 minutos
def carregar_dados_privados():
    """Carrega a planilha de um repositório privado do GitHub usando um token."""
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_url = st.secrets["PRIVATE_REPO_URL"]
    except KeyError:
        st.error("Segredos do GitHub (TOKEN ou URL) não configurados. Contate o administrador.")
        return pd.DataFrame()

    headers = {"Authorization": f"token {token}"}
    response = requests.get(repo_url, headers=headers)

    if response.status_code == 200:
        df = pd.read_excel(BytesIO(response.content))
        # ... (lógica de limpeza de dados) ...
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
    else:
        st.error(f"Falha ao acessar os dados privados. Status: {response.status_code}")
        return pd.DataFrame()

df = carregar_dados_privados()

# ==============================================================================
# 3. O RESTANTE DO DASHBOARD (SIDEBAR, FILTROS, GRÁFICOS)
# ==============================================================================
# O código daqui para baixo é idêntico à nossa última versão funcional do Streamlit.
# Nenhuma alteração é necessária na interface.

# Paleta de Cores Mosaic
MOSAIC_COLORS = {"azul_escuro": "#002776", "azul_claro": "#00AEEF", "verde": "#78BE20", "teal": "#007C91"}

st.sidebar.image("assets/logo.png", width=200)
st.sidebar.title("Painel de Controle")
st.sidebar.markdown("---")

if not df.empty:
    ccs_options = ['(Todos)'] + sorted(df['Centro custo'].unique())
    cc_selecionado = st.sidebar.selectbox("Filtrar por Centro de Custo:", options=ccs_options)

    data_min = df['Data de lançamento'].min().date()
    data_max = df['Data de lançamento'].max().date()
    data_inicio = st.sidebar.date_input("Data Inicial:", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = st.sidebar.date_input("Data Final:", value=data_max, min_value=data_inicio, max_value=data_max)

    tipos_doc_options = ['(Todos)'] + sorted(df['Tipo de documento'].unique())
    tipo_doc_selecionado = st.sidebar.selectbox("Filtrar por Tipo de Documento:", options=tipos_doc_options)

    df_filtrado = df.copy()
    if cc_selecionado != '(Todos)':
        df_filtrado = df_filtrado[df_filtrado['Centro custo'] == cc_selecionado]
    if tipo_doc_selecionado != '(Todos)':
        df_filtrado = df_filtrado[df_filtrado['Tipo de documento'] == tipo_doc_selecionado]
    df_filtrado = df_filtrado[(df_filtrado['Data de lançamento'].dt.date >= data_inicio) & (df_filtrado['Data de lançamento'].dt.date <= data_fim)]

    st.markdown('<p class="main-header">Dashboard Corporativo de Custos</p>', unsafe_allow_html=True)
    # ... O restante do layout (KPIs, gráficos, tabela) continua aqui ...
    # (código omitido por brevidade, mas é o mesmo da versão anterior)
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if not df_filtrado.empty:
            # ... KPIs ...
            total_custo = df_filtrado['Valor/MR'].sum()
            num_lancamentos = len(df_filtrado)
            ticket_medio = total_custo / num_lancamentos if num_lancamentos > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Custo Total no Período", f"R$ {total_custo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col2.metric("Nº de Lançamentos", f"{num_lancamentos}")
            col3.metric("Custo Médio/Lançamento", f"R$ {ticket_medio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        st.markdown('</div>', unsafe_allow_html=True)

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        # ... Gráfico de linha ...
        st.markdown('<div class="card">', unsafe_allow_html=True)
        custo_mensal = df_filtrado.groupby('Ano-Mês')['Valor/MR'].sum().reset_index()
        fig_linha = px.line(custo_mensal, x='Ano-Mês', y='Valor/MR', title="Evolução do Custo Mensal", markers=True, color_discrete_sequence=[MOSAIC_COLORS['azul_claro']])
        fig_linha.update_layout(plot_bgcolor='white', title_font_size=20, height=450)
        st.plotly_chart(fig_linha, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_graf2:
        # ... Gráfico de barras ...
        st.markdown('<div class="card">', unsafe_allow_html=True)
        custo_por_classe = df_filtrado.groupby('Classe de Custo')['Valor/MR'].sum().nlargest(10).sort_values()
        fig_barras = px.bar(custo_por_classe, x='Valor/MR', y=custo_por_classe.index, orientation='h', text=custo_por_classe.values, color_discrete_sequence=[MOSAIC_COLORS['teal']])
        fig_barras.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
        fig_barras.update_layout(title_text="Top 10 Classes de Custo", plot_bgcolor='white', yaxis={'categoryorder':'total ascending'}, title_font_size=20, height=450)
        st.plotly_chart(fig_barras, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("Não foi possível carregar os dados. Verifique a configuração de segredos.")