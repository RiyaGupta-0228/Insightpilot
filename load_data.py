import pandas as pd
import sqlite3

print("Reading CSV file...")
df = pd.read_csv("online_retail_II.csv", encoding="ISO-8859-1")

print(f"Columns found: {list(df.columns)}")

df.columns = ["invoice", "stock_code", "description", "quantity",
              "invoice_date", "unit_price", "customer_id", "country"]

df = df.dropna(subset=["customer_id"])
df["customer_id"] = df["customer_id"].astype(int)

conn = sqlite3.connect("retail.db")
df.to_sql("transactions", conn, if_exists="replace", index=False)

count = pd.read_sql("SELECT COUNT(*) AS n FROM transactions", conn)
print(f"Done! Loaded {count['n'][0]:,} rows into retail.db")
conn.close()
