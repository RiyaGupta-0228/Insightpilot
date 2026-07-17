from google import genai
import os
import sqlite3
import pandas as pd

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

question = input("Ask a question about the retail data: ")

prompt = f"""You are a SQL expert. Given this SQLite table:

Table: transactions
Columns: invoice (TEXT), stock_code (TEXT), description (TEXT),
quantity (INTEGER), invoice_date (TEXT), unit_price (REAL),
customer_id (INTEGER), country (TEXT)

Note: cancelled orders have negative quantity. Exclude them from revenue calculations.

Write a SQLite query to answer: "{question}"

Return ONLY the SQL query, no explanation, no markdown formatting.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

sql = response.text.strip().replace("```sql", "").replace("```", "").strip()

print("\nAI-generated SQL:")
print(sql)

conn = sqlite3.connect("retail.db")
try:
    result = pd.read_sql(sql, conn)
    print("\nAnswer:")
    print(result)
except Exception as e:
    print("\nQuery failed! Error:")
    print(e)
conn.close()
