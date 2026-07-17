from google import genai
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """You are a SQL expert. Given this SQLite table:

Table: transactions
Columns: invoice (TEXT), stock_code (TEXT), description (TEXT),
quantity (INTEGER), invoice_date (TEXT), unit_price (REAL),
customer_id (INTEGER), country (TEXT)

Note: cancelled orders have negative quantity. Exclude them from revenue calculations.

Write a SQLite query to answer: "Which countries generate the most revenue?"

Return ONLY the SQL query, no explanation, no markdown formatting.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)
print("AI-generated SQL:")
print(response.text)
