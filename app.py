import streamlit as st
import plotly.express as px
from pipeline import check_intent, generate_sql, summarize_results
from validator import validate_sql
import sqlite3
import pandas as pd

st.set_page_config(page_title="InsightPilot", page_icon="📊", layout="wide")

st.title("📊 InsightPilot")
st.caption("Ask questions about 824K retail transactions in plain English")

# Example question buttons - one click instead of typing
examples = [
    "Which countries generate the most revenue?",
    "Who are the top 10 customers by total spending?",
    "What are the 5 best-selling products?",
    "What was the monthly revenue trend in 2010?",
]
cols = st.columns(len(examples))
clicked = None
for col, ex in zip(cols, examples):
    if col.button(ex, use_container_width=True):
        clicked = ex

question = st.text_input("Your question:",
    value=clicked or "",
    placeholder="e.g. Which countries generate the most revenue?")

if question:
    try:
        with st.spinner("Checking if this is answerable..."):
            answerable = check_intent(question)
    except RuntimeError:
        st.info("The AI service is experiencing high demand right now. "
                "Please try again in a few minutes.")
        st.stop()
    with st.spinner(""):
        if not answerable:
            st.warning("This question can't be answered from the retail data. "
                       "Try asking about revenue, products, customers, or countries.")
            st.stop()

    with st.spinner("Generating and validating SQL..."):
        error = None
        sql = None
        for attempt in range(3):
            candidate = generate_sql(question, previous_error=error)
            ok, reason = validate_sql(candidate)
            if ok:
                sql = candidate
                break
            error = reason
        if sql is None:
            st.error(f"Couldn't generate valid SQL. Last error: {error}")
            st.stop()

    conn = sqlite3.connect("retail.db")
    result = pd.read_sql(sql, conn)
    conn.close()

    try:
        with st.spinner("Writing insight..."):
            insight = summarize_results(question, sql, result)
    except RuntimeError:
        insight = "Insight generation is temporarily unavailable (high demand) - but the data below is complete."
        insight = insight.replace("`", "")   # strip stray markdown

    st.success(insight)

    col1, col2 = st.columns([2, 1])

    # Detect ID-like columns: numeric, but really categories
    id_like = [c for c in result.columns
               if c.lower().endswith("_id") or c.lower() == "id"]
    display = result.copy()
    for c in id_like:
        display[c] = display[c].astype(str)

    with col1:
        st.subheader("Data")
        # Format remaining numeric columns with commas + 2 decimals
        fmt = {c: "{:,.2f}" for c in display.select_dtypes("number").columns}
        st.dataframe(display.style.format(fmt), use_container_width=True)

    with col2:
        st.subheader("Chart")
        text_cols = display.select_dtypes(include="object").columns
        num_cols = display.select_dtypes(include="number").columns
        if len(text_cols) >= 1 and len(num_cols) >= 1 and 2 <= len(display) <= 25:
            fig = px.bar(display.head(15), x=text_cols[0], y=num_cols[0])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No obvious chart for this result shape.")

    with st.expander("View generated SQL"):
        st.code(sql, language="sql")
