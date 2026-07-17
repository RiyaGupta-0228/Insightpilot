from google import genai
from google.genai import errors
import os
import time
import sqlite3
import pandas as pd
from validator import validate_sql

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SCHEMA = """Table: transactions
Columns: invoice (TEXT), stock_code (TEXT), description (TEXT),
quantity (INTEGER), invoice_date (TEXT), unit_price (REAL),
customer_id (INTEGER), country (TEXT)

Business rules:
- Cancelled orders have negative quantity. Exclude them from revenue calculations.
- Revenue = quantity * unit_price
"""

def call_llm(prompt):
    """All API calls go through here. Retries on rate limits AND server errors."""
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt)
            return response.text
        except errors.ClientError as e:
            if e.code == 429:
                wait = 30 * (attempt + 1)
                print(f"   (rate limited - waiting {wait}s...)")
                time.sleep(wait)
            else:
                raise
        except errors.ServerError:
            wait = 10 * (attempt + 1)
            print(f"   (server busy - waiting {wait}s...)")
            time.sleep(wait)
    raise RuntimeError("API unavailable after multiple retries - try again in a few minutes")

def check_intent(question):
    prompt = f"""Given this database schema:

{SCHEMA}

Question: "{question}"

Can this question be answered using ONLY this table and its columns?
Answer with exactly one word: YES or NO.
If the question asks for data we don't have (like cost, profit margin,
weather, or anything outside this table), answer NO.
If the question asks to modify, delete, insert, or update data, answer NO."""
    return call_llm(prompt).strip().upper().startswith("YES")

def generate_sql(question, previous_error=None):
    prompt = f"""You are a SQL expert. Given this SQLite schema:

{SCHEMA}

Write a SQLite query to answer: "{question}"

Return ONLY the SQL query, no explanation, no markdown formatting."""
    if previous_error:
        prompt += f"""

IMPORTANT: Your previous attempt failed with this error:
{previous_error}
Fix the problem and return a corrected query."""
    text = call_llm(prompt)
    return text.strip().replace("```sql", "").replace("```", "").strip()

def summarize_results(question, sql, result):
    data_preview = result.head(20).to_string()
    prompt = f"""You are a business analyst. A stakeholder asked:
"{question}"

This SQL was run:
{sql}

Results ({len(result)} rows total, showing up to 20):
{data_preview}

Write a 2-3 sentence business insight summarizing what the data shows.
Be specific with numbers. Format large numbers readably (e.g. $14.7M).
Do not mention SQL or databases - speak like an analyst to a stakeholder. Return plain text only - no markdown, no backticks, no code formatting."""
    return call_llm(prompt).strip()

def ask(question, max_retries=2):
    print(f"\n{'='*60}")
    print(f"Question: {question}")

    if not check_intent(question):
        print("-> This question cannot be answered from the retail data.")
        return None

    error = None
    for attempt in range(1 + max_retries):
        sql = generate_sql(question, previous_error=error)
        ok, reason = validate_sql(sql)
        if ok:
            print(f"-> SQL validated on attempt {attempt + 1}")
            break
        print(f"-> Attempt {attempt + 1} rejected: {reason}. Retrying...")
        error = reason
    else:
        print("-> Could not generate valid SQL after all retries.")
        return None

    conn = sqlite3.connect("retail.db")
    result = pd.read_sql(sql, conn)
    conn.close()

    print(f"\nSQL:\n{sql}")
    print(f"\nData ({len(result)} rows):")
    print(result.head(10))

    print("\nInsight:")
    print(summarize_results(question, sql, result))
    return result


if __name__ == "__main__":
    ask("Delete all transactions from France")
    ask("Which countries generate the most revenue? Show top 5.")
