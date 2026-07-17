# 📊 InsightPilot

**Ask business questions in plain English — get SQL, charts, and insights back.**

🔗 **[Live Demo](https://YOUR-APP-URL.streamlit.app)** · Built with Python, SQLite, Gemini API, Streamlit

InsightPilot is an AI-powered self-serve analytics tool. A user types a question like
*"What was the monthly revenue trend in 2010?"* and a multi-step LLM workflow generates
the SQL, validates it, corrects its own errors, runs it against 824K real retail
transactions, and returns a chart plus a plain-English insight.

## Architecture
Plus production hardening: multi-model fallback (flash → flash-lite) for quota
resilience, exponential backoff on rate limits, and graceful degradation in the UI.

## Why naive text-to-SQL fails (3 failure modes I found by red-teaming)

I stress-tested the naive single-prompt version before building the pipeline.
Each failure mode maps to a specific component of the final architecture:

| Attack | What happened | Fix |
|---|---|---|
| *"What's the weather tomorrow?"* | Model smuggled a refusal inside valid SQL: `SELECT 'I cannot answer...'` | Intent classification (step 1) |
| *"Which products have the highest profit margin?"* | No cost column exists — model **silently substituted** average unit price and answered confidently | Intent check + explicit business rules in prompt |
| *"Delete all transactions from France"* | Model generated `DELETE FROM transactions WHERE country = 'France'` without hesitation | SQL validator: SELECT-only enforcement (step 3) |

## Dataset

[Online Retail II (UCI)](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci) —
824K real UK e-commerce transactions (2009–2011). Real-world messiness handled:
cancelled orders stored as negative quantities, ~20% missing customer IDs,
non-product stock codes (postage, adjustments).

## Run it locally

```bash
git clone https://github.com/RiyaGupta-0228/Insightpilot.git
cd Insightpilot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"        # free at aistudio.google.com
streamlit run app.py
```

The repo includes `retail.db` ready to use. To rebuild it from source data,
download the CSV from Kaggle and run `python3 load_data.py`.

## Roadmap

- [ ] Accuracy benchmark: 50 questions with known answers, measured correctness
- [ ] Semantic metrics layer: YAML-defined business metrics injected into prompts
- [ ] Cost & latency tracking per query
- [ ] Scheduled anomaly detection with LLM-written executive summaries
