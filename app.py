
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

# Converte o número do mês para o nome em português
df["Mes_Nome"] = df["Mes_Num"].apply(
    lambda x: meses_pt[int(x) - 1] if pd.notna(x) else None
)


# -------------------------------------------------------------------
# FILTROS NA BARRA LATERAL
# -------------------------------------------------------------------
st.sidebar.header("Filtros de Análise")

# Filtro de ano
anos_disponiveis = sorted(df["Ano"].dropna().unique())

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

if not df_filtrado.empty:

    # Temperatura máxima
    idx_max = df_filtrado["Temp. Max. (C)"].idxmax()
    row_max = df_filtrado.loc[idx_max]

    temp_max_val = row_max["Temp. Max. (C)"]
    data_max_val = row_max["data_hora_utc"].strftime(
        "%d/%m/%Y às %H:%M"
    )

    # Temperatura mínima
    idx_min = df_filtrado["Temp. Min. (C)"].idxmin()
    row_min = df_filtrado.loc[idx_min]

    temp_min_val = row_min["Temp. Min. (C)"]
    data_min_val = row_min["data_hora_utc"].strftime(
        "%d/%m/%Y às %H:%M"
    )

    # Chuva e umidade
    chuva_total = df_filtrado["Chuva (mm)"].sum()
    umidade_media = df_filtrado["Umi. Ins. (%)"].mean()

else:
    temp_max_val, data_max_val = 0, "N/A"
    temp_min_val, data_min_val = 0, "N/A"
    chuva_total, umidade_media = 0, 0


# Exibição dos indicadores
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🌡️ Temp. Máxima",
    f"{temp_max_val:.1f} °C"
)
col1.caption(f"📅 Ocorrido em: {data_max_val}")

col2.metric(
    "❄️ Temp. Mínima",
    f"{temp_min_val:.1f} °C"
)
col2.caption(f"📅 Ocorrido em: {data_min_val}")

col3.metric(
    "🌧️ Chuva Acumulada",
    f"{chuva_total:.1f} mm"
)

col4.metric(
    "💧 Umidade Média",
    f"{umidade_media:.1f} %"
)


# -------------------------------------------------------------------
# GRÁFICOS INTERATIVOS
# -------------------------------------------------------------------
st.markdown("---")

# Evolução térmica
st.subheader("Evolução Térmica (Máximas e Mínimas)")

fig_temp = px.line(
    df_filtrado,
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


# -------------------------------------------------------------------
# PRECIPITAÇÃO ACUMULADA
# -------------------------------------------------------------------
st.subheader("Precipitação Acumulada")

if ano_escolhido == "Todos os Anos":

    chuva_agrupada = (
        df_filtrado.groupby("Ano")["Chuva (mm)"]
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
        df_filtrado.groupby(["Mes_Num", "Mes_Nome"])["Chuva (mm)"]
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
        category_orders={"Mes_Nome": meses_pt}
    )

st.plotly_chart(
    fig_chuva,
    use_container_width=True
)
