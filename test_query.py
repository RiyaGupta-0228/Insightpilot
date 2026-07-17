import sqlite3
import pandas as pd

conn = sqlite3.connect("retail.db")
result = pd.read_sql("""
    SELECT country, ROUND(SUM(quantity * unit_price), 2) AS revenue
    FROM transactions
    WHERE quantity > 0
    GROUP BY country
    ORDER BY revenue DESC
    LIMIT 5
""", conn)
print(result)
conn.close()
