import pandas as pd

df = pd.read_parquet(
    "data/processed/censo_municipio_rs_2024.parquet"
)

print(df.shape)
print(df.columns.tolist())