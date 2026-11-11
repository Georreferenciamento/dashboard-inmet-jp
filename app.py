import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

# -------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Meteorológico - INMET",
    layout="wide"
)
st.title("📊 Painel Meteorológico (INMET - João Pessoa)")

# -------------------------------------------------------------------
# CARREGAMENTO DOS DADOS E CÁLCULO DE SENSAÇÃO TÉRMICA
# -------------------------------------------------------------------
@st.cache_data
def carregar_dados():
    df = pd.read_parquet("meteorologia_inmet_2000_2026_tratado.parquet")  
    
    # Garante que a coluna seja do tipo data
    df["data_hora_utc"] = pd.to_datetime(df["data_hora_utc"])
    
    # Cálculo da Sensação Térmica (Temperatura Aparente - Steadman / BOM)
    def calcular_sensacao(row):
        t = row.get("Temp. Max. (C)")
        rh = row.get("Umi. Ins. (%)")
        if pd.isna(t) or pd.isna(rh):
            return np.nan
        e = (rh / 100.0) * 6.105 * np.exp((17.27 * t) / (237.7 + t))
        return t + 0.33 * e - 4.00

    if "Temp. Max. (C)" in df.columns and "Umi. Ins. (%)" in df.columns:
        df["Sensacao_Termica"] = df.apply(calcular_sensacao, axis=1)
        
    return df

df = carregar_dados()

# -------------------------------------------------------------------
# COLUNAS AUXILIARES DE DATA
# -------------------------------------------------------------------
df["Ano"] = df["data_hora_utc"].dt.year
df["Mes_Num"] = df["data_hora_utc"].dt.month

# Nomes dos meses em português
meses_pt = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
df["Mes_Nome"] = df["Mes_Num"].apply(
    lambda x: meses_pt[int(x) - 1] if pd.notna(x) else None
)

# -------------------------------------------------------------------
# FILTROS NA BARRA LATERAL
# -------------------------------------------------------------------
st.sidebar.header("Filtros de Análise")

anos_disponiveis = sorted(df["Ano"].dropna().unique(), reverse=True)
ano_escolhido = st.sidebar.selectbox(
    "Selecione o Ano",
    ["Todos os Anos"] + list(anos_disponiveis)
)

if ano_escolhido != "Todos os Anos":
    df_filtrado = df[df["Ano"] == int(ano_escolhido)]
else:
    df_filtrado = df.copy()

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
st.subheader(f"📈 Indicadores Principais ({ano_escolhido} / {mes_escolhido})")
st.caption("🕒 Horários em UTC (UTC-3 em relação a João Pessoa).")
st.markdown("📌 **Fonte dos dados:** [INMET - Tabela de Estações (A320)](https://tempo.inmet.gov.br/TabelaEstacoes/A320)", unsafe_allow_html=True)
st.markdown("---")

# Inicialização dos indicadores
temp_max_val = None
data_max_val = "N/D"
sensacao_max_val = None
temp_min_val = None
data_min_val = "N/D"
chuva_total = None
umidade_media = None

if not df_filtrado.empty:
    # Temperatura Máxima
    dados_max = df_filtrado.dropna(subset=["Temp. Max. (C)"])
    if not dados_max.empty:
        idx_max = dados_max["Temp. Max. (C)"].idxmax()
        row_max = dados_max.loc[idx_max]
        temp_max_val = row_max["Temp. Max. (C)"]
        data_max_val = row_max["data_hora_utc"].strftime("%d/%m/%Y às %H:%M")

    # Sensação Térmica Máxima
    if "Sensacao_Termica" in df_filtrado.columns:
        dados_sensacao = df_filtrado.dropna(subset=["Sensacao_Termica"])
        if not dados_sensacao.empty:
            sensacao_max_val = dados_sensacao["Sensacao_Termica"].max()

    # Temperatura Mínima
    dados_min = df_filtrado.dropna(subset=["Temp. Min. (C)"])
    if not dados_min.empty:
        idx_min = dados_min["Temp. Min. (C)"].idxmin()
        row_min = dados_min.loc[idx_min]
        temp_min_val = row_min["Temp. Min. (C)"]
        data_min_val = row_min["data_hora_utc"].strftime("%d/%m/%Y às %H:%M")

    # Chuva Acumulada
    dados_chuva = df_filtrado["Chuva (mm)"].dropna()
    if not dados_chuva.empty:
        chuva_total = dados_chuva.sum()

    # Umidade Média
    dados_umidade = df_filtrado["Umi. Ins. (%)"].dropna()
    if not dados_umidade.empty:
        umidade_media = dados_umidade.mean()

# -------------------------------------------------------------------
# EXIBIÇÃO DOS INDICADORES (5 Colunas)
# -------------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("🌡️ Temp. Máxima", f"{temp_max_val:.1f} °C" if temp_max_val is not None else "N/D")
col1.caption(f"📅 {data_max_val}")

col2.metric("🥵 Sensação Máx.", f"{sensacao_max_val:.1f} °C" if sensacao_max_val is not None else "N/D")
col2.caption("⚡ Pico de abafamento")

col3.metric("❄️ Temp. Mínima", f"{temp_min_val:.1f} °C" if temp_min_val is not None else "N/D")
col3.caption(f"📅 {data_min_val}")

col4.metric("🌧️ Chuva Acum.", f"{chuva_total:.1f} mm" if chuva_total is not None else "N/D")

col5.metric("💧 Umidade Média", f"{umidade_media:.1f} %" if umidade_media is not None else "N/D")

# -------------------------------------------------------------------
# AVISOS SOBRE AUSÊNCIA DE DADOS
# -------------------------------------------------------------------
if df_filtrado.empty:
    st.warning("Não existem registros para o período selecionado.")

# -------------------------------------------------------------------
# GRÁFICOS INTERATIVOS
# -------------------------------------------------------------------
st.markdown("---")

# Evolução Térmica
st.subheader("Evolução Térmica (Máximas e Mínimas)")
dados_temp = df_filtrado.dropna(subset=["Temp. Max. (C)", "Temp. Min. (C)"], how="all")

if not dados_temp.empty:
    fig_temp = px.line(
        dados_temp,
        x="data_hora_utc",
        y=["Temp. Max. (C)", "Temp. Min. (C)"],
        labels={"data_hora_utc": "Data e Hora", "value": "Temperatura (°C)", "variable": "Métrica"}
    )
    st.plotly_chart(fig_temp, use_container_width=True)
else:
    st.info("Não existem dados de temperatura para gerar o gráfico neste período.")

# Precipitação Acumulada
st.subheader("Precipitação Acumulada")
dados_chuva_grafico = df_filtrado.dropna(subset=["Chuva (mm)"])

if not dados_chuva_grafico.empty:
    if ano_escolhido == "Todos os Anos":
        chuva_agrupada = dados_chuva_grafico.groupby("Ano")["Chuva (mm)"].sum().reset_index()
        fig_chuva = px.bar(chuva_agrupada, x="Ano", y="Chuva (mm)", title="Chuva Acumulada por Ano", color="Chuva (mm)")
    else:
        chuva_agrupada = dados_chuva_grafico.groupby(["Mes_Num", "Mes_Nome"])["Chuva (mm)"].sum().reset_index().sort_values("Mes_Num")
        fig_chuva = px.bar(chuva_agrupada, x="Mes_Nome", y="Chuva (mm)", title=f"Chuva Acumulada por Mês em {ano_escolhido}", color="Chuva (mm)", category_orders={"Mes_Nome": meses_pt})
    st.plotly_chart(fig_chuva, use_container_width=True)
else:
    st.info("Não existem dados de precipitação para gerar o gráfico neste período.") 

# -------------------------------------------------------------------
# TOP 10 MAIORES TEMPERATURAS MÁXIMAS 
# -------------------------------------------------------------------
st.markdown("---")
st.subheader(f"🔥 Top 10 Maiores Temperaturas Máximas ({ano_escolhido} / {mes_escolhido})")

coluna_temp_max = "Temp. Max. (C)"

if not df_filtrado.empty and coluna_temp_max in df_filtrado.columns:
    top_10_temp = df_filtrado.nlargest(10, coluna_temp_max)[["data_hora_utc", coluna_temp_max]].copy()
    top_10_temp["data_hora_utc"] = top_10_temp["data_hora_utc"].dt.strftime("%d/%m/%Y %H:%M")
    top_10_temp = top_10_temp.rename(columns={
        "data_hora_utc": "Data e Hora (UTC)",
        coluna_temp_max: "Temperatura Máxima (°C)"
    })
    st.dataframe(top_10_temp, use_container_width=False, hide_index=True)
else:
    st.warning("Não há dados suficientes para exibir o Top 10 de temperatura no período selecionado.")

# -------------------------------------------------------------------
# TOP 10 MAIORES SENSAÇÕES TÉRMICAS 
# -------------------------------------------------------------------
st.markdown("---")
st.subheader(f"🥵 Top 10 Maiores Sensações Térmicas ({ano_escolhido} / {mes_escolhido})")
st.caption("Dias em que a combinação entre a temperatura real e a alta umidade gerou maior sensação de abafamento.")

coluna_sensacao = "Sensacao_Termica"

if not df_filtrado.empty and coluna_sensacao in df_filtrado.columns:
    top_10_sensacao = df_filtrado.nlargest(10, coluna_sensacao)[["data_hora_utc", coluna_sensacao, "Temp. Max. (C)", "Umi. Ins. (%)"]].copy()
    top_10_sensacao["data_hora_utc"] = top_10_sensacao["data_hora_utc"].dt.strftime("%d/%m/%Y %H:%M")
    top_10_sensacao = top_10_sensacao.rename(columns={
        "data_hora_utc": "Data e Hora (UTC)",
        coluna_sensacao: "Sensação Térmica (°C)",
        "Temp. Max. (C)": "Temp. Real (°C)",
        "Umi. Ins. (%)": "Umidade (%)"
    })
    st.dataframe(top_10_sensacao, use_container_width=False, hide_index=True)
else:
    st.warning("Não há dados suficientes para exibir o Top 10 de sensação térmica no período selecionado.")
