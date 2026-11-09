import glob
import os
import urllib.request
import zipfile
import numpy as np
import pandas as pd

nome_parquet = "meteorologia_inmet_2000_2026_tratado.parquet"
nome_csv = "meteorologia_inmet_2000_2026_tratado.csv"

# 1. Carregar base existente para descobrir a última data registada
ultima_data = None
df_existente = pd.DataFrame()

if os.path.exists(nome_parquet):
  print("📂 A carregar base de dados existente...")
  df_existente = pd.read_parquet(nome_parquet)
  if "data_hora_utc" in df_existente.columns and not df_existente.empty:
    df_existente["data_hora_utc"] = pd.to_datetime(
        df_existente["data_hora_utc"]
    )
    ultima_data = df_existente["data_hora_utc"].max()
    print(f"🕒 Último registo existente na base: {ultima_data}")
else:
  print(
      "ℹ️ Nenhuma base anterior encontrada. Será gerada uma nova a partir do"
      " zero."
  )

# 2. Tentar atualizar o ficheiro mais recente do INMET (ex: 2026)
url_zip = "https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip"
zip_nome = "2026.zip"

print("\n🔄 A tentar ligar ao portal do INMET...")
try:
  urllib.request.urlretrieve(url_zip, zip_nome)
  print("✅ Download concluído!")
  with zipfile.ZipFile(zip_nome, "r") as z:
    for filename in z.namelist():
      if "A320" in filename or "JOAO PESSOA" in filename.upper():
        z.extract(filename, ".")
        print(f"🎯 Ficheiro extraído: {filename}")
  os.remove(zip_nome)
except Exception as e:
  print(
      "⚠️ Download automático ignorado/bloqueado pela rede. A usar ficheiros"
      " locais..."
  )
  if os.path.exists(zip_nome):
    os.remove(zip_nome)

# 3. Ler todos os ficheiros fonte disponíveis na pasta
arquivos = [
    arq
    for arq in glob.glob("*.csv") + glob.glob("*.txt")
    if not arq.startswith("meteorologia_inmet") and arq != "requirements.txt"
]

print(f"\n📁 Encontrados {len(arquivos)} ficheiros fonte para análise.")

df_list = []
for arq in arquivos:
  try:
    header_row = None
    with open(arq, "r", encoding="latin1", errors="ignore") as f:
      for idx, line in enumerate(f):
        if "data" in line.lower() and "hora" in line.lower():
          header_row = idx
          break

    if header_row is None:
      continue

    df = pd.read_csv(
        arq,
        sep=";",
        encoding="latin1",
        skiprows=header_row,
        low_memory=False,
        decimal=",",
    )
    df.columns = df.columns.str.strip().str.replace('"', "", regex=False)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    col_data, col_hora = None, None
    for col in df.columns:
      if col.lower() == "data":
        col_data = col
      elif "hora" in col.lower():
        col_hora = col

    if col_data and col_hora:
      df = df.rename(columns={col_data: "Data", col_hora: "Hora (UTC)"})
      df = df[df["Data"].astype(str).str.match(r"\d{2}/\d{2}/\d{4}")]
      df_list.append(df)
  except Exception as e:
    print(f"Erro ao ler {arq}: {e}")

if not df_list and df_existente.empty:
  raise ValueError("Nenhum dado válido encontrado para processar.")

if df_list:
  # Combina dados brutos lidos
  df_novo_bruto = pd.concat(df_list, ignore_index=True)

  # Tratamento de Data e Hora UTC
  hora_str = df_novo_bruto["Hora (UTC)"].astype(str).str.zfill(4)
  hora_fmt = hora_str.str.replace(r"(\d{2})(\d{2})", r"\1:\2", regex=True)
  data_hora_str = df_novo_bruto["Data"] + " " + hora_fmt
  df_novo_bruto["data_hora_utc"] = pd.to_datetime(
      data_hora_str, format="%d/%m/%Y %H:%M", errors="coerce"
  )

  # Tipagem numérica rigorosa
  colunas_ignorar = ["Data", "Hora (UTC)", "data_hora_utc"]
  for col in df_novo_bruto.columns:
    if col not in colunas_ignorar:
      if df_novo_bruto[col].dtype == object:
        df_novo_bruto[col] = (
            df_novo_bruto[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
      df_novo_bruto[col] = df_novo_bruto[col].replace(
          ["", "nan", "NaN", "None", "-9999", "-9999.0", "null"], np.nan
      )
      df_novo_bruto[col] = pd.to_numeric(df_novo_bruto[col], errors="coerce")

  # 4. Aplicação da Carga Incremental
  if ultima_data is not None:
    # Filtra apenas o que está à frente da última data já guardada
    df_novos_filtrados = df_novo_bruto[
        df_novo_bruto["data_hora_utc"] > ultima_data
    ]
    print(
        f"⚡ Encontrados {len(df_novos_filtrados)} novos registos horários após"
        f" {ultima_data}."
    )

    if not df_novos_filtrados.empty:
      df_final = pd.concat(
          [df_existente, df_novos_filtrados], ignore_index=True
      )
    else:
      print(
          "👍 A base já está totalmente atualizada. Nenhum registo novo para"
          " acrescentar."
      )
      df_final = df_existente.copy()
  else:
    df_final = df_novo_bruto.copy()

  # Limpeza final de duplicatas e ordenação cronológica segura
  df_final = (
      df_final.dropna(subset=["data_hora_utc"])
      .drop_duplicates(subset=["data_hora_utc"])
      .sort_values("data_hora_utc")
      .reset_index(drop=True)
  )

  # 5. Exportação otimizada
  df_final.to_parquet(nome_parquet, index=False)
  df_final.to_csv(nome_csv, index=False, decimal=".")

  print("\n✨ Processo de atualização incremental concluído com sucesso!")
  print(f"💾 Base guardada em: {nome_parquet}")
  print(f"📈 Total consolidado na base: {len(df_final):,} registos horários.")
else:
  print("Nenhum ficheiro novo lido, mantendo a base atual.")
