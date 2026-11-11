import pandas as pd
import plotly.express as px
import streamlit as st

# -------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Meteorológico - INMET",
    layout="wide"
)
st.title("📊 Painel Meteorológico (INMET - João Pessoa)")
# -------------------------------------------------------------------
# CARREGAMENTO DOS DADOS
# -------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    df = pd.read_parquet("meteorologia_inmet_2000_2026_tratado.parquet")  
    return df
df = carregar_dados()

# Garante que a coluna seja do tipo data
df["data_hora_utc"] = pd.to_datetime(df["data_hora_utc"])
# -------------------------------------------------------------------
# COLUNAS AUXILIARES DE DATA
# -------------------------------------------------------------------
df["Ano"] = df["data_hora_utc"].dt.year
df["Mes_Num"] = df["data_hora_utc"].dt.month

# Nomes dos meses em português
meses_pt = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"
]
df["Mes_Nome"] = df["Mes_Num"].apply(
    lambda x: meses_pt[int(x) - 1] if pd.notna(x) else None
)
# -------------------------------------------------------------------
# FILTROS NA BARRA LATERAL
# -------------------------------------------------------------------
st.sidebar.header("Filtros de Análise")

# Filtro de ano
anos_disponiveis = sorted(df["Ano"].dropna().unique(), reverse=True)
ano_escolhido = st.sidebar.selectbox(
    "Selecione o Ano",
    ["Todos os Anos"] + list(anos_disponiveis)
)
if ano_escolhido != "Todos os Anos":
    df_filtrado = df[df["Ano"] == int(ano_escolhido)]
else:
    df_filtrado = df.copy()

# Filtro de mês

meses_disponiveis = [
    mes for mes in meses_pt
    if mes in df_filtrado["Mes_Nome"].values
]

mes_escolhido = st.sidebar.selectbox(
    "Selecione o Mês",
    ["Todos os Meses"] + meses_disponiveis
)

if mes_escolhido != "Todos os Meses":
    df_filtrado = df_filtrado[
        df_filtrado["Mes_Nome"] == mes_escolhido
    ]
# -------------------------------------------------------------------
# INDICADORES PRINCIPAIS (KPIs)
# -------------------------------------------------------------------
st.subheader(

    f"📈 Indicadores Principais ({ano_escolhido} / {mes_escolhido})"

)
st.caption("🕒 Horários em UTC (UTC-3 em relação a João Pessoa).")
st.markdown("📌 **Fonte dos dados:** [INMET - Tabela de Estações (A320)](https://tempo.inmet.gov.br/TabelaEstacoes/A320)", unsafe_allow_html=True)
st.markdown("---")

# Inicialização dos indicadores

temp_max_val = None
data_max_val = "N/D"
temp_min_val = None
data_min_val = "N/D"
chuva_total = None
umidade_media = None
if not df_filtrado.empty:
    # ---------------------------------------------------------------
    # TEMPERATURA MÁXIMA
    # ---------------------------------------------------------------

    dados_max = df_filtrado.dropna(
        subset=["Temp. Max. (C)"]
    )
    if not dados_max.empty:
        idx_max = dados_max["Temp. Max. (C)"].idxmax()
        row_max = dados_max.loc[idx_max]
        temp_max_val = row_max["Temp. Max. (C)"]
        data_max_val = row_max["data_hora_utc"].strftime(
            "%d/%m/%Y às %H:%M"
        )
    # ---------------------------------------------------------------
    # TEMPERATURA MÍNIMA
    # ---------------------------------------------------------------
    dados_min = df_filtrado.dropna(

        subset=["Temp. Min. (C)"]

    )
    if not dados_min.empty:
        idx_min = dados_min["Temp. Min. (C)"].idxmin()
        row_min = dados_min.loc[idx_min]
        temp_min_val = row_min["Temp. Min. (C)"]
        data_min_val = row_min["data_hora_utc"].strftime(
            "%d/%m/%Y às %H:%M"
        )
    # ---------------------------------------------------------------
    # CHUVA ACUMULADA
    # ---------------------------------------------------------------

    dados_chuva = df_filtrado["Chuva (mm)"].dropna()
    if not dados_chuva.empty:
        chuva_total = dados_chuva.sum()
    # ---------------------------------------------------------------
    # UMIDADE MÉDIA
    # ---------------------------------------------------------------

    dados_umidade = df_filtrado["Umi. Ins. (%)"].dropna()
    if not dados_umidade.empty:

        umidade_media = dados_umidade.mean()
# -------------------------------------------------------------------
# EXIBIÇÃO DOS INDICADORES
# -------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🌡️ Temp. Máxima",
    f"{temp_max_val:.1f} °C" if temp_max_val is not None else "N/D"
)
col1.caption(
    f"📅 Ocorrido em: {data_max_val}"
)
col2.metric(
    "❄️ Temp. Mínima",
    f"{temp_min_val:.1f} °C" if temp_min_val is not None else "N/D"
)
col2.caption(
    f"📅 Ocorrido em: {data_min_val}"
)

col3.metric(
    "🌧️ Chuva Acumulada",
    f"{chuva_total:.1f} mm" if chuva_total is not None else "N/D"
)

col4.metric(
    "💧 Umidade Média",
    f"{umidade_media:.1f} %" if umidade_media is not None else "N/D"
)
# -------------------------------------------------------------------
# AVISOS SOBRE AUSÊNCIA DE DADOS
# -------------------------------------------------------------------

if df_filtrado.empty:
    st.warning(
        "Não existem registros para o período selecionado."
    )
elif (
    temp_max_val is None
    and temp_min_val is None
    and chuva_total is None
    and umidade_media is None

):
    st.warning(
        "Existem registros, mas não há dados meteorológicos válidos para este período."
    )

# -------------------------------------------------------------------
# GRÁFICOS INTERATIVOS
# -------------------------------------------------------------------

st.markdown("---")

# ---------------------------------------------------------------
# EVOLUÇÃO TÉRMICA
# ---------------------------------------------------------------

st.subheader("Evolução Térmica (Máximas e Mínimas)")
dados_temp = df_filtrado.dropna(
    subset=["Temp. Max. (C)", "Temp. Min. (C)"],
    how="all"
)

if not dados_temp.empty:
    fig_temp = px.line(
        dados_temp,
        x="data_hora_utc",
        y=["Temp. Max. (C)", "Temp. Min. (C)"],

        labels={
            "data_hora_utc": "Data e Hora",
            "value": "Temperatura (°C)",
            "variable": "Métrica"
        }
    )

    st.plotly_chart(
        fig_temp,
        use_container_width=True

    )
else:
    st.info(
        "Não existem dados de temperatura para gerar o gráfico neste período."
    )
# -------------------------------------------------------------------
# PRECIPITAÇÃO ACUMULADA
# -------------------------------------------------------------------

st.subheader("Precipitação Acumulada")
dados_chuva_grafico = df_filtrado.dropna(
    subset=["Chuva (mm)"]
)
if not dados_chuva_grafico.empty:
    if ano_escolhido == "Todos os Anos":


        chuva_agrupada = (
            dados_chuva_grafico
            .groupby("Ano")["Chuva (mm)"]
            .sum()
            .reset_index()

        )

        fig_chuva = px.bar(
            chuva_agrupada,
            x="Ano",
            y="Chuva (mm)",
            title="Chuva Acumulada por Ano",
            color="Chuva (mm)"
        )
    else:
        chuva_agrupada = (
            dados_chuva_grafico
            .groupby(["Mes_Num", "Mes_Nome"])["Chuva (mm)"]
            .sum()
            .reset_index()
            .sort_values("Mes_Num")

        )

        fig_chuva = px.bar(
            chuva_agrupada,
            x="Mes_Nome",
            y="Chuva (mm)",
            title=f"Chuva Acumulada por Mês em {ano_escolhido}",
            color="Chuva (mm)",
            category_orders={
                "Mes_Nome": meses_pt
            }
        )
    st.plotly_chart(
        fig_chuva,
        use_container_width=True
    )

else:
    st.info(
        "Não existem dados de precipitação para gerar o gráfico neste período."
    ) 
# -------------------------------------------------------------------
# TOP 10 MAIORES TEMPERATURAS MÁXIMAS
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("🔥 Top 10 Maiores Temperaturas Máximas")

# Verifica se a coluna de temperatura máxima existe antes de processar
coluna_temp_max = "Temp. Max. (C)"

if coluna_temp_max in df.columns:
    # Seleciona os 10 maiores registos da coluna correta
    top_10_temp = df.nlargest(10, coluna_temp_max)
    
    # Exibe as colunas principais de interesse formatadas
    colunas_exibir = [col for col in ["data_hora_utc", coluna_temp_max, "Temp. Min. (C)", "Chuva (mm)", "Umi. Ins. (%)"] if col in df.columns]
    
    st.dataframe(top_10_temp[colunas_exibir], use_container_width=True)
else:
    st.error(f"A coluna '{coluna_temp_max}' não foi encontrada na base de dados.")

