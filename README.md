# WhisperQL

Natural Language → SQL · Powered by LLMs

### Speak softly, query loudly.

> Type a plain-English question. Get SQL. Execute and See results.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![LLM](https://img.shields.io/badge/Gen_AI-4285F4?style=flat&logo=google&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)

---

## What is WhisperQL?

**WhisperQL** is a full-stack AI-powered web application that bridges the gap between human language and database queries. Instead of writing complex SQL, you simply ask a question in plain English — WhisperQL figures out the rest.

Under the hood, it introspects your PostgreSQL database schema, passes it along with your question to **LLM of Users choice**, receives a SQL query back, executes it, and displays the results as a clean interactive table — all in seconds.

If the generated query fails, WhisperQL automatically retries up to **3 times**, feeding the error back to the LLM so it can self-correct. Think of it as a SQL developer that never sleeps and never complains.

```
You:        "Show me the top 5 customers by total order value this year"
WhisperQL:  SELECT c.name, SUM(o.total) AS revenue
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE EXTRACT(YEAR FROM o.created_at) = 2025
            GROUP BY c.name
            ORDER BY revenue DESC
            LIMIT 5;
Result:     ✓ 5 rows · 2 cols · 0.43s
```

---

## Features

- 🧠 **Natural Language to SQL** — Converts plain-English questions into accurate SQL using LLMs
- 🔍 **Auto Schema Introspection** — Automatically reads your database structure so the LLM always has context
- ♻️ **Self-Healing Queries** — Retries up to 3 times with error context if a query fails, so the LLM can fix itself
- 🛡️ **Review Before Execute** — Generated SQL is shown for review before running — no accidental destructive queries
- 📜 **Query History** — Last 10 queries tracked in session with success/failure status
- ⚡ **FastAPI Backend** — Clean REST API with schema, query, history, and health endpoints
- 🎨 **Dark UI** — Sleek dark-themed Streamlit frontend with syntax-highlighted SQL output
- 🧪 **Fully Tested** — pytest test suite with mocks — no real DB or API calls needed

---

## Tech Stack

| Layer          | Technology                           |
| -------------- | ------------------------------------ |
| **Frontend**   | Streamlit                            |
| **Backend**    | Python 3.10+ · FastAPI · Uvicorn     |
| **Database**   | PostgreSQL · psycopg2                |
| **LLM**        | Gemini · Claude · GPT (Users choice) |
| **Validation** | Pydantic                             |
| **Testing**    | pytest                               |

---

## Project Structure

```
whisperql/
├── backend/
|   ├── app/
│   |  ├── main.py          # FastAPI app — /schema, /generate, /execute, /history, /health
│   |  ├── db.py            # PostgreSQL connection + schema introspection
│   |  ├── llm.py           # LLM gateway (Google Gemini 3 Flash)
│   |  └── models.py        # Pydantic request/response models
|   ├── tests/
│   |  ├── test_db.py       # Database connection & schema tests
│   |  ├── test_llm.py      # LLM prompt & response tests
|   |  └── test_api.py      # FastAPI endpoint integration tests
|
├── frontend/
|   ├── streamlit_app.py     # Streamlit frontend (WhisperQL UI)
|
├── .env                 # Environment variables (never commit this)
├── .env.example         # Example env file for reference
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL instance (local or remote)
- Google AI Studio API key ([get one free here](https://aistudio.google.com/apikey)) Or Other LLMs API KEY

---

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/whisperql.git
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/your_database
```

| Variable         | Description                   | Required |
| ---------------- | ----------------------------- | -------- |
| `GOOGLE_API_KEY` | Your Google AI Studio API key | ✅ Yes   |
| `DATABASE_URL`   | PostgreSQL connection string  | ✅ Yes   |

> **Never commit your `.env` file.** It is already in `.gitignore`.

---

### 5. Start the FastAPI backend

```bash
uvicorn backend.app.main:app --reload
```

The API will be running at `http://localhost:8000`.

Verify it's alive:

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

Interactive API docs are available at `http://localhost:8000/docs`.

---

### 6. Start the Streamlit frontend

Open a **separate terminal** (with the virtual environment activated):

```bash
streamlit run frontend/streamlit_app.py
```

The app opens at `http://localhost:8501`.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        WhisperQL Flow                       │
└─────────────────────────────────────────────────────────────┘

  User types question
         │
         ▼
  ┌─────────────┐     schema      ┌──────────────┐
  │  Streamlit  │ ──────────────► │   FastAPI    │
  │  Frontend   │                 │   Backend    │
  └─────────────┘ ◄────────────── └──────┬───────┘
         │           SQL + results       │
         │                               │ question + schema
         │                               ▼
         │                        ┌──────────────┐
         │                        │    LLM       │
         │                        └──────┬───────┘
         │                               │ SQL query
         │                               ▼
         │                        ┌──────────────┐
         │                        │  PostgreSQL  │
         │                        │   Database   │
         └────────────────────────└──────────────┘
```

1. **Load Schema** — Enter your database credentials in the sidebar and click Load Schema. WhisperQL introspects your database and stores the schema (tables, columns, types) in memory.

2. **Ask a Question** — Type any plain-English question about your data in the query box.

3. **Generate SQL** — WhisperQL sends your question + schema to Gemini 3 Flash, which returns a SQL query tailored to your exact database structure.

4. **Review** — The generated SQL is displayed with syntax highlighting. You can inspect it before running anything.

5. **Execute** — Click Execute Query to run it against your database. Results appear as an interactive table.

6. **Self-Healing** — If the query throws an error, WhisperQL automatically retries up to 3 times, sending the error message back to the LLM so it can understand what went wrong and generate a corrected query.

---

### LLM Provider

WhisperQL uses **Google Gemini 3 Flash** via the `google-generativeai` SDK. It is fast, free-tier friendly, and highly capable for structured output tasks like SQL generation.

Get your free API key at [Google AI Studio](https://aistudio.google.com/apikey) — no credit card required.

To swap to a different LLM provider, update `LLM PROVIDER in .env`.

---

## Security Notes

- **WhisperQL shows generated SQL before executing** — always review queries before running them on production databases.
- Use a **read-only database user** for WhisperQL in production environments to prevent any accidental writes.
- Never expose your `.env` file or commit API keys to version control.
- Consider adding rate limiting to the FastAPI backend if deploying publicly.

---

## Roadmap

- [ ] Query explanation mode ("explain this SQL in plain English")
- [ ] Multi-turn conversational queries ("now filter that by date...")
- [ ] Docker Compose setup for one-command deployment

---

<div align="center">

** WhisperQL** · Speak softly, query loudly.

Built using FastAPI · Streamlit · Google Gemini · PostgreSQL

Developed By Aadarsh

</div>
