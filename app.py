import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Dashboard Meteorológico - INMET João Pessoa",
    page_icon="🌤️",
    layout="wide"
)

# Carregamento dos dados com cache para otimizar a performance
@st.cache_data
def carregar_dados():
    df = pd.read_parquet('meteorologia_inmet_2000_2026_tratado.parquet')
    
    # Garante que a coluna 'ano' existe extraindo-a do campo de data/hora se não estiver presente
    if 'ano' not in df.columns and 'data_hora_utc' in df.columns:
        df['ano'] = pd.to_datetime(df['data_hora_utc']).dt.year
        
    return df

df = carregar_dados()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("⚙️ Filtros")

# 1. Ajuste da ordem dos anos (do mais recente para o mais antigo)
anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox(
    "Selecione o Ano:",
    options=anos_disponiveis,
    help="Os registos seguem o padrão UTC (Hora Universal)."
)

# 2. Nota informativa sobre o fuso horário
st.sidebar.markdown("---")
st.sidebar.caption("🕒 **Fuso Horário:** Os dados são apresentados no padrão UTC (INMET). Para obter o horário local de João Pessoa, subtraia 3 horas (UTC-3).")

# --- CORPO PRINCIPAL DO DASHBOARD ---
st.title("🌤️ Dashboard Meteorológico — João Pessoa / PB")
st.markdown(f"Exibindo dados consolidados de **2000 a 2026** *(Ano selecionado: **{ano_selecionado}**)*")

# Filtrar dados pelo ano selecionado
df_filtrado = df[df['ano'] == ano_selecionado]

# Métrica rápida do ano selecionado
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Registos", f"{len(df_filtrado):,}")
with col2:
    temp_max = df_filtrado['temperatura_c'].max() if 'temperatura_c' in df_filtrado.columns else "N/A"
    st.metric("Temp. Máxima", f"{temp_max} °C" if temp_max != "N/A" else "N/A")
with col3:
    temp_min = df_filtrado['temperatura_c'].min() if 'temperatura_c' in df_filtrado.columns else "N/A"
    st.metric("Temp. Mínima", f"{temp_min} °C" if temp_min != "N/A" else "N/A")
with col4:
    precip_total = df_filtrado['precipitacao_mm'].sum() if 'precipitacao_mm' in df_filtrado.columns else "N/A"
    st.metric("Chuva Acumulada", f"{precip_total:.1f} mm" if isinstance(precip_total, (int, float)) else "N/A")

st.divider()

# Exibição dos dados filtrados
st.subheader(f"📊 Registos do Ano de {ano_selecionado}")
st.dataframe(df_filtrado, use_container_width=True)
